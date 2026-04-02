from __future__ import annotations

from pipeline.reviews_polars import RAW_DATA_PATH, PROCESSED_DIR, cleaned_reviews_lazy


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "reviews_cleaned.parquet"
    cleaned_reviews = cleaned_reviews_lazy(RAW_DATA_PATH).collect(engine="streaming")
    cleaned_reviews.write_parquet(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
