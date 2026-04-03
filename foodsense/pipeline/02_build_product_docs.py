"""
02_build_product_docs.py — Construction des documents produit agrégés
Outil : Polars
Entrée  : data/processed/reviews_clean.parquet
Sortie  : data/processed/product_docs.parquet
          data/samples/product_docs_sample.parquet (500 produits)
"""

import polars as pl
from pathlib import Path

# ─── CHEMINS ──────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent
INPUT_PATH   = BASE_DIR / "data" / "processed" / "reviews_clean.parquet"
OUTPUT_PATH  = BASE_DIR / "data" / "processed" / "product_docs.parquet"
SAMPLE_PATH  = BASE_DIR / "data" / "samples"   / "product_docs_sample.parquet"
SAMPLE_SIZE  = 500

def build_texte_recherche(titres: list, avis: list) -> str:
    """Construit le texte à encoder : titres + 3 premiers avis, tronqué à 2000 chars."""
    titres_str = " | ".join([t for t in titres if t])
    avis_str   = " ".join(avis[:3])
    texte      = f"{titres_str} . {avis_str}"
    return texte[:2000]

def main():
    print("📦 Chargement reviews_clean.parquet...")
    df = pl.read_parquet(INPUT_PATH)
    print(f"   Lignes : {len(df):,}")

    print("🔧 Agrégation par produit...")
    df_agg = (
        df
        .group_by("ProductId")
        .agg([
            pl.col("Score").mean().round(2).alias("note_moyenne"),
            pl.col("Score").count().alias("nb_avis"),
            pl.col("Summary").alias("tous_les_titres"),
            pl.col("Text").alias("tous_les_avis"),
        ])
    )

    print("📝 Construction du texte_recherche et extraits_utiles...")
    # Construire texte_recherche et extraits_utiles ligne par ligne
    records = []
    for row in df_agg.iter_rows(named=True):
        texte = build_texte_recherche(
            row["tous_les_titres"],
            row["tous_les_avis"]
        )
        extraits = row["tous_les_avis"][:5]
        records.append({
            "product_id"     : row["ProductId"],
            "note_moyenne"   : row["note_moyenne"],
            "nb_avis"        : row["nb_avis"],
            "texte_recherche": texte,
            "extraits_utiles": extraits,
        })

    df_produit = pl.DataFrame({
        "product_id"     : [r["product_id"]      for r in records],
        "note_moyenne"   : [r["note_moyenne"]     for r in records],
        "nb_avis"        : [r["nb_avis"]          for r in records],
        "texte_recherche": [r["texte_recherche"]  for r in records],
        "extraits_utiles": [r["extraits_utiles"]  for r in records],
    })

    print(f"✅ Produits uniques : {len(df_produit):,}")

    # Sauvegarder dataset complet
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_produit.write_parquet(OUTPUT_PATH)
    print(f"✅ Sauvegardé → {OUTPUT_PATH}")

    # Sauvegarder échantillon 500 produits pour les tests
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_produit.sample(n=SAMPLE_SIZE, seed=42).write_parquet(SAMPLE_PATH)
    print(f"✅ Échantillon ({SAMPLE_SIZE}) → {SAMPLE_PATH}")

    print("\n   Aperçu :")
    print(df_produit.select([
        "product_id", "note_moyenne", "nb_avis", "texte_recherche"
    ]).head(3))

if __name__ == "__main__":
    main()