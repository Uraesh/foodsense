import polars as pl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "raw" / "Reviews.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "reviews_clean.parquet"


def main():
    print("Chargement du dataset...")
    df = pl.read_csv(
        RAW_PATH,
        columns=[
            "Id",
            "ProductId",
            "UserId",
            "HelpfulnessNumerator",
            "HelpfulnessDenominator",
            "Score",
            "Time",
            "Summary",
            "Text",
        ],
        infer_schema_length=10000,
        ignore_errors=True,
    )
    print(f"Lignes brutes : {len(df):,}")

    df = (
        df.drop_nulls(subset=["ProductId", "Text", "Score"])
        .with_columns(
            [
                pl.col("Summary").str.strip_chars().fill_null("").alias("Summary"),
                pl.col("Text").str.strip_chars().alias("Text"),
            ]
        )
        .filter(pl.col("Score").is_between(1, 5))
        .unique(subset=["ProductId", "Text"], keep="first")
    )

    print(f"Lignes apres nettoyage : {len(df):,}")
    print(f"Colonnes : {df.columns}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUTPUT_PATH)
    print(f"Sauvegarde OK -> {OUTPUT_PATH}")
    print(df.head(3))


if __name__ == "__main__":
    main()
