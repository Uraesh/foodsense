"""Build product documents from cleaned reviews."""
from __future__ import annotations

import polars as pl

from pipeline.reviews_polars import PROCESSED_DIR, build_product_documents


def main() -> None:
    """Main function to build product documents and export to Parquet."""
    input_path = PROCESSED_DIR / "reviews_cleaned.parquet"
    output_path = PROCESSED_DIR / "product_documents.parquet"
    cleaned_reviews = pl.read_parquet(input_path)
    product_documents = build_product_documents(cleaned_reviews)
    product_documents.write_parquet(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
