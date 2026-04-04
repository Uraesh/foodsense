import polars as pl
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
INPUT_PATH  = BASE_DIR / "data" / "processed" / "reviews_clean.parquet"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "product_docs.parquet"
SAMPLE_PATH = BASE_DIR / "data" / "samples" / "product_docs_sample.parquet"
SAMPLE_SIZE = 500

def main():
    print("Chargement reviews_clean.parquet...")
    df = pl.read_parquet(INPUT_PATH)
    print(f"Lignes : {len(df):,}")

    df_produit = (
        df
        .group_by("ProductId")
        .agg([
            pl.col("Score").mean().round(2).alias("note_moyenne"),
            pl.col("Score").count().alias("nb_avis"),
            pl.col("Summary").alias("tous_les_titres"),
            pl.col("Text").alias("tous_les_avis"),
            pl.col("HelpfulnessNumerator").mean().round(2).alias("helpfulness_moy"),
        ])
        .with_columns([
            pl.concat_str([
                pl.col("tous_les_titres").list.join(" | "),
                pl.lit(" . "),
                pl.col("tous_les_avis").list.slice(0, 3).list.join(" "),
            ]).str.slice(0, 2000).alias("texte_recherche"),
            pl.col("tous_les_avis").list.slice(0, 5).alias("extraits_utiles"),
        ])
        .select([
            pl.col("ProductId").alias("product_id"),
            "note_moyenne",
            "nb_avis",
            "helpfulness_moy",
            "texte_recherche",
            "extraits_utiles",
        ])
    )

    print(f"Produits uniques : {len(df_produit):,}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_produit.write_parquet(OUTPUT_PATH)
    print(f"Sauvegarde OK -> {OUTPUT_PATH}")
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_produit.sample(n=SAMPLE_SIZE, seed=42).write_parquet(SAMPLE_PATH)
    print(f"Echantillon ({SAMPLE_SIZE}) -> {SAMPLE_PATH}")
    print(df_produit.select([
        "product_id", "note_moyenne", "nb_avis", "texte_recherche"
    ]).head(3))

if __name__ == "__main__":
    main()