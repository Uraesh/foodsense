"""
03_generate_embeddings.py — Génération des embeddings par batch via Ollama
Outil : Ollama qwen3-embedding:0.6b
Entrée  : data/processed/product_docs.parquet
Sortie  : data/processed/product_embeddings.parquet
"""

import polars as pl
import ollama
from pathlib import Path
import time

# ─── CONFIG ───────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent.parent
INPUT_PATH     = BASE_DIR / "data" / "processed" / "product_docs.parquet"
OUTPUT_PATH    = BASE_DIR / "data" / "processed" / "product_embeddings.parquet"
SAMPLE_PATH    = BASE_DIR / "data" / "samples"   / "product_docs_sample.parquet"

EMBED_MODEL    = "qwen3-embedding:0.6b"
BATCH_SIZE     = 50
USE_SAMPLE     = True   # ← True = 500 produits (test rapide) | False = 74 258 (complet)
# ──────────────────────────────────────────────────────

def generate_embedding(text: str) -> list[float]:
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]

def main():
    # Choisir dataset complet ou échantillon
    path = SAMPLE_PATH if USE_SAMPLE else INPUT_PATH
    print(f"📦 Chargement : {path.name}...")
    df = pl.read_parquet(path)
    total = len(df)
    print(f"   Produits à encoder : {total:,}")

    # Vérifier qu'Ollama tourne
    print(f"🔌 Test connexion Ollama ({EMBED_MODEL})...")
    try:
        test = generate_embedding("test connexion")
        print(f"✅ Ollama OK — dimension vecteur : {len(test)}")
    except Exception as e:
        print(f"❌ Ollama non disponible : {e}")
        print("   Lance 'ollama serve' dans un autre terminal")
        return

    # Génération des embeddings
    print(f"\n🚀 Génération embeddings (batch={BATCH_SIZE})...")
    product_ids = []
    embeddings  = []
    errors      = 0
    start       = time.time()

    for i, row in enumerate(df.iter_rows(named=True)):
        try:
            vector = generate_embedding(row["texte_recherche"])
            product_ids.append(row["product_id"])
            embeddings.append(vector)
        except Exception as e:
            errors += 1
            print(f"  ⚠️  Erreur {row['product_id']} : {e}")

        # Progression tous les 50
        if (i + 1) % BATCH_SIZE == 0 or (i + 1) == total:
            elapsed = time.time() - start
            pct     = (i + 1) / total * 100
            eta     = (elapsed / (i + 1)) * (total - i - 1)
            print(f"  📊 {i+1}/{total} ({pct:.1f}%) — "
                  f"écoulé: {elapsed:.0f}s — "
                  f"ETA: {eta:.0f}s — "
                  f"erreurs: {errors}")

    # Construire le DataFrame résultat
    df_embed = pl.DataFrame({
        "product_id": product_ids,
        "embedding" : embeddings,
    })

    # Joindre avec les métadonnées
    df_final = df.join(df_embed, on="product_id", how="inner")

    # Sauvegarder
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.write_parquet(OUTPUT_PATH)

    elapsed_total = time.time() - start
    print(f"\n✅ Embeddings générés : {len(df_final):,}")
    print(f"   Erreurs            : {errors}")
    print(f"   Temps total        : {elapsed_total:.0f}s")
    print(f"   Sauvegardé → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()