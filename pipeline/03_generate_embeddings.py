from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Iterable

import httpx
import polars as pl

from pipeline.reviews_polars import PROCESSED_DIR, SAMPLES_DIR

PROJECT_ROOT = PROCESSED_DIR.parents[1]


def iter_texts(df: pl.DataFrame) -> Iterable[tuple[str, str]]:
    for row in df.iter_rows(named=True):
        yield row["ProductId"], row["search_text"]


def embed_text(client: httpx.Client, base_url: str, model: str, text: str) -> list[float]:
    response = client.post(
        f"{base_url}/api/embeddings",
        json={"model": model, "prompt": text},
    )
    response.raise_for_status()
    data = response.json()
    return data["embedding"]


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def write_status(status_path: Path, payload: dict[str, object]) -> None:
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate embeddings with Ollama qwen3-embedding:0.6b.")
    parser.add_argument(
        "--model",
        default="qwen3-embedding:0.6b",
        help="Ollama embedding model name.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama base URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Use the sample product documents dataset.",
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
        "--status-path",
        type=Path,
        default=PROJECT_ROOT / "embedding_status.json",
        help="Path of the progress status file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = (
        SAMPLES_DIR / "product_documents_sample.parquet"
        if args.use_sample
        else PROCESSED_DIR / "product_documents.parquet"
    )
    slug = model_slug(args.model)
    output_path = PROCESSED_DIR / f"product_embeddings_{slug}.parquet"
    manifest_path = PROCESSED_DIR / f"embedding_manifest_{slug}.json"
    status_path = args.status_path

    product_documents = pl.read_parquet(input_path)
    if args.limit > 0:
        product_documents = product_documents.head(args.limit)

    total = product_documents.height
    if total == 0:
        raise SystemExit("No product documents found for embedding.")

    start = time.time()
    embeddings: list[list[float]] = []
    product_ids: list[str] = []
    errors = 0
    error_samples: list[str] = []

    base_status = {
        "stage": "starting",
        "model": args.model,
        "base_url": args.base_url,
        "use_sample": args.use_sample,
        "limit": args.limit,
        "max_chars": args.max_chars,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
        "products_total": total,
        "products_processed": 0,
        "products_embedded": 0,
        "errors": 0,
        "duration_sec": 0.0,
        "eta_sec": None,
    }
    write_status(status_path, base_status)

    with httpx.Client(timeout=60.0) as client:
        # Quick connectivity check + vector size
        test_embedding = embed_text(client, args.base_url, args.model, "test")
        vector_size = len(test_embedding)
        base_status["stage"] = "running"
        base_status["vector_size"] = vector_size
        write_status(status_path, base_status)

        progress_every = 1 if total <= 50 else 50

        for idx, (product_id, text) in enumerate(iter_texts(product_documents), start=1):
            try:
                safe_text = str(text) if text is not None else ""
                if args.max_chars > 0 and len(safe_text) > args.max_chars:
                    safe_text = safe_text[: args.max_chars]
                vector = embed_text(client, args.base_url, args.model, safe_text)
                product_ids.append(product_id)
                embeddings.append(vector)
            except Exception as exc:
                errors += 1
                if len(error_samples) < 5:
                    error_samples.append(f"{product_id}: {exc}")

            if idx % progress_every == 0 or idx == total:
                elapsed = time.time() - start
                pct = idx / total * 100
                eta = (elapsed / idx) * (total - idx) if idx else 0
                write_status(
                    status_path,
                    {
                        **base_status,
                        "stage": "running",
                        "products_processed": idx,
                        "products_embedded": len(embeddings),
                        "errors": errors,
                        "duration_sec": round(elapsed, 2),
                        "eta_sec": round(eta, 2),
                        "progress_pct": round(pct, 2),
                        "error_samples": error_samples,
                    },
                )
                print(f"{idx}/{total} ({pct:.1f}%) - elapsed {elapsed:.0f}s - eta {eta:.0f}s - errors {errors}")

    if not embeddings:
        details = "; ".join(error_samples) if error_samples else "No details"
        write_status(
            status_path,
            {
                **base_status,
                "stage": "failed",
                "products_processed": total,
                "products_embedded": 0,
                "errors": errors,
                "duration_sec": round(time.time() - start, 2),
                "eta_sec": 0,
                "error_samples": error_samples,
                "message": details,
            },
        )
        raise SystemExit(f"No embeddings generated. Sample errors: {details}")

    embed_df = pl.DataFrame({"ProductId": product_ids, "embedding": embeddings})
    final_df = product_documents.join(embed_df, on="ProductId", how="inner")
    final_df.write_parquet(output_path)

    manifest = {
        "model": args.model,
        "base_url": args.base_url,
        "vector_size": vector_size,
        "products_total": total,
        "products_embedded": final_df.height,
        "errors": errors,
        "use_sample": args.use_sample,
        "limit": args.limit,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "duration_sec": round(time.time() - start, 2),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_status(
        status_path,
        {
            **base_status,
            "stage": "completed",
            "products_processed": total,
            "products_embedded": final_df.height,
            "errors": errors,
            "duration_sec": round(time.time() - start, 2),
            "eta_sec": 0,
            "progress_pct": 100.0,
            "error_samples": error_samples,
            "vector_size": vector_size,
        },
    )
    print(f"Wrote {output_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
