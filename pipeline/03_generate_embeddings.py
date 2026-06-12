"""Generate embeddings for product documents using Ollama."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable

import httpx
import polars as pl

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.reviews_polars import PROCESSED_DIR

from urllib.parse import quote_plus


def load_env_defaults() -> None:
    """Charge les variables d'environnement par défaut à partir des fichiers .env."""
    for env_path in (PROJECT_ROOT / ".env.example", PROJECT_ROOT / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def database_url_from_env() -> str:
    """Construit l'URL de connexion à la base de données à partir des variables d'environnement."""
    load_env_defaults()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "Foodsense")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASS", "")

    if password:
        return f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{database}"
    return f"postgresql://{user}@{host}:{port}/{database}"


PROJECT_ROOT = PROCESSED_DIR.parents[1]


def iter_texts(
    df: pl.DataFrame, id_column: str, text_column: str
) -> Iterable[tuple[str, str]]:
    """Itère sur les lignes du DataFrame en extrayant les colonnes d'identifiant et de texte."""
    for row in df.iter_rows(named=True):
        yield row[id_column], row[text_column]


def embed_text(
    client: httpx.Client, base_url: str, model: str, text: str
) -> list[float]:
    """Envoie une requête à l'API d'Ollama pour obtenir l'embedding du texte donné."""
    response = client.post(
        f"{base_url}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]


def model_slug(model: str) -> str:
    """Génère un slug sûr pour le nom du modèle, utilisé dans les noms de fichiers."""
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def write_status(status_path: Path, payload: dict[str, object]) -> None:
    """Écrit le statut d'avancement dans un fichier JSON pour suivi en temps réel."""
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Analyse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings with Ollama from PostgreSQL documents."
    )
    parser.add_argument(
        "--model",
        default=os.getenv("EMBEDDING_MODEL", "bge-m3"),
        help="Ollama embedding model name.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama base URL.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional custom parquet output path.",
    )
    parser.add_argument(
        "--id-column",
        default="source_product_id",
        help="Column containing the stable product identifier.",
    )
    parser.add_argument(
        "--text-column",
        default="search_text",
        help="Column containing the text to embed.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of products (0 = all).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1200,
        help="Max characters per text sent to the embedding model.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25,
        help="Write live progress every N embedded documents.",
    )
    parser.add_argument(
        "--status-path",
        type=Path,
        default=PROJECT_ROOT / "embedding_status.json",
        help="Path of the progress status file.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=100,
        help="Save embeddings to disk every N products.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing output file and restart from scratch.",
    )
    return parser.parse_args()


def _flush_checkpoint(
    output_path: Path,
    existing_df: pl.DataFrame | None,
    id_column: str,
    product_ids: list[str],
    embeddings: list[list[float]],
    product_documents: pl.DataFrame,
) -> pl.DataFrame:
    """Écrit les nouveaux embeddings accumulés en les fusionnant proprement sans doublons."""
    embed_df = pl.DataFrame({id_column: product_ids, "embedding": embeddings})
    new_df = product_documents.filter(pl.col(id_column).is_in(product_ids)).join(
        embed_df, on=id_column, how="inner"
    )

    if existing_df is not None:
        merged = pl.concat([existing_df, new_df])
    else:
        merged = new_df

    merged.write_parquet(output_path)
    return merged


def main() -> None:
    """Point d'entrée principal du script de génération d'embeddings."""
    args = parse_args()
    slug = model_slug(args.model)
    output_path = (
        args.output_path or PROCESSED_DIR / f"product_embeddings_{slug}.parquet"
    )
    manifest_path = PROCESSED_DIR / f"embedding_manifest_{slug}.json"
    status_path = args.status_path

    # --- Connexion et lecture depuis PostgreSQL ---
    print("Connexion à PostgreSQL pour extraire les documents de recherche...")
    db_url = database_url_from_env()
    query = f"SELECT {args.id_column}, {args.text_column} FROM foodsense_v2.product_search_documents"
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    try:
        product_documents = pl.read_database_uri(query, uri=db_url)
    except Exception as e:
        raise SystemExit(
            f"Erreur lors de la lecture de PostgreSQL (La base est-elle peuplée ?) : {e}"
        )

    total_database_records = product_documents.height
    if total_database_records == 0:
        raise SystemExit(
            "La table 'product_search_documents' est vide. Lance d'abord le script d'ingestion (05)."
        )

    # --- Gestion de la reprise (Resume) ---
    existing_df: pl.DataFrame | None = None
    already_done: set[str] = set()
    if output_path.exists() and not args.no_resume:
        try:
            existing_df = pl.read_parquet(output_path)
            already_done = set(existing_df[args.id_column].to_list())
            print(
                f"Reprise détectée : {len(already_done)} produits déjà vectorisés ignorés."
            )
            product_documents = product_documents.filter(
                ~pl.col(args.id_column).is_in(already_done)
            )
        except Exception:
            print("Fichier de sauvegarde corrompu. On recommence à zéro.")
            existing_df = None

    remaining_total = product_documents.height
    if remaining_total == 0:
        print("Tous les produits trouvés en base de données ont déjà été vectorisés.")
        return

    start = time.time()
    embeddings: list[list[float]] = []
    product_ids: list[str] = []
    errors = 0
    error_samples: list[str] = []

    base_status = {
        "stage": "starting",
        "model": args.model,
        "base_url": args.base_url,
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
        "products_total": total_database_records,
        "already_done": len(already_done),
        "products_remaining": remaining_total,
        "errors": 0,
        "duration_sec": 0.0,
    }
    write_status(status_path, base_status)

    with httpx.Client(timeout=60.0) as client:
        test_embedding = embed_text(client, args.base_url, args.model, "test")
        vector_size = len(test_embedding)
        base_status["stage"] = "running"
        base_status["vector_size"] = vector_size
        write_status(status_path, base_status)

        progress_every = max(1, args.progress_every)
        checkpoint_every = max(1, args.checkpoint_every)

        for idx, (source_product_id, text) in enumerate(
            iter_texts(product_documents, args.id_column, args.text_column),
            start=1,
        ):
            try:
                safe_text = str(text) if text is not None else ""
                if args.max_chars > 0 and len(safe_text) > args.max_chars:
                    safe_text = safe_text[: args.max_chars]

                vector = embed_text(client, args.base_url, args.model, safe_text)
                product_ids.append(source_product_id)
                embeddings.append(vector)
            except Exception as exc:
                errors += 1
                if len(error_samples) < 5:
                    error_samples.append(f"{source_product_id}: {exc}")

            if idx % progress_every == 0 or idx == remaining_total:
                elapsed = time.time() - start
                pct = (idx / remaining_total) * 100
                eta = (elapsed / idx) * (remaining_total - idx) if idx else 0

                write_status(
                    status_path,
                    {
                        **base_status,
                        "stage": "running",
                        "current_product_id": source_product_id,
                        "products_processed_session": idx,
                        "products_embedded_total": len(already_done) + idx - errors,
                        "errors": errors,
                        "duration_sec": round(elapsed, 2),
                        "eta_sec": round(eta, 2),
                        "session_progress_pct": round(pct, 2),
                        "error_samples": error_samples,
                    },
                )
                print(
                    f"Progression : {idx}/{remaining_total} ({pct:.1f}%) - Écoulé: {elapsed:.0f}s - ETA: {eta:.0f}s - Erreurs: {errors}"
                )

            # --- Sauvegarde et vidage de la RAM ---
            if len(embeddings) > 0 and len(embeddings) % checkpoint_every == 0:
                existing_df = _flush_checkpoint(
                    output_path,
                    existing_df,
                    args.id_column,
                    product_ids,
                    embeddings,
                    product_documents,
                )
                print(
                    f"  [Checkpoint] {len(embeddings)} éléments purgés et synchronisés sur le disque."
                )
                # Réinitialisation pour éviter l'effet d'accumulation de doublons
                product_ids = []
                embeddings = []

        # Vidage final s'il reste des éléments dans la liste
        if len(embeddings) > 0:
            existing_df = _flush_checkpoint(
                output_path,
                existing_df,
                args.id_column,
                product_ids,
                embeddings,
                product_documents,
            )

    final_df = pl.read_parquet(output_path)

    manifest = {
        "model": args.model,
        "base_url": args.base_url,
        "vector_size": vector_size,
        "products_total": total_database_records,
        "products_embedded": final_df.height,
        "errors": errors,
        "output_path": str(output_path),
        "duration_sec": round(time.time() - start, 2),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write_status(
        status_path,
        {
            **base_status,
            "stage": "completed",
            "products_embedded_total": final_df.height,
            "errors": errors,
            "duration_sec": round(time.time() - start, 2),
            "eta_sec": 0,
        },
    )
    print(
        f"Traitement terminé avec succès.\nFichier Parquet : {output_path}\nManifeste : {manifest_path}"
    )


if __name__ == "__main__":
    main()
