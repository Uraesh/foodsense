"""
01_clean.py — Nettoyage du dataset Amazon Fine Food Reviews
Outil : Polars
Entrée  : data/raw/Reviews.csv
Sortie  : data/processed/reviews_clean.parquet
"""

import polars as pl
from pathlib import Path

# ─── CHEMINS ──────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
RAW_PATH    = BASE_DIR / "data" / "raw" / "Reviews.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "reviews_clean.parquet"

def main():
    print("📦 Chargement du dataset...")
    df = pl.read_csv(
        RAW_PATH,
        columns=["ProductId", "Score", "Summary", "Text"],
        infer_schema_length=10000,
        ignore_errors=True,
    )
    print(f"   Lignes brutes : {len(df):,}")

    print("🧹 Nettoyage...")
    df = (
        df
        # Supprimer les nulls sur colonnes critiques
        .drop_nulls(subset=["ProductId", "Text", "Score"])

        # Nettoyer les espaces
        .with_columns([
            pl.col("Summary").str.strip_chars().alias("Summary"),
            pl.col("Text").str.strip_chars().alias("Text"),
        ])

        # Remplacer Summary vide par chaîne vide
        .with_columns([
            pl.col("Summary").fill_null("").alias("Summary"),
        ])

        # Garder uniquement scores valides
        .filter(pl.col("Score").is_between(1, 5))

        # Supprimer doublons exacts sur ProductId + Text
        .unique(subset=["ProductId", "Text"], keep="first")
    )

    print(f"   Lignes après nettoyage : {len(df):,}")

    # Créer le dossier processed si nécessaire
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder en Parquet
    df.write_parquet(OUTPUT_PATH)
    print(f"✅ Sauvegardé → {OUTPUT_PATH}")
    print(f"   Colonnes : {df.columns}")
    print(f"   Aperçu :")
    print(df.head(3))

if __name__ == "__main__":
    main()