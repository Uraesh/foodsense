#!/usr/bin/env python3
"""Inspect V2 parquet files and display schema + sample rows."""
import sys
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def inspect_file(filepath: Path) -> None:
    """Inspect a parquet file: schema, column types, row count, and sample."""
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return

    frame = pl.read_parquet(filepath)
    print(f"\n📄 File: {filepath.name}")
    print(f"   Shape: {frame.shape[0]} rows × {frame.shape[1]} columns")
    print(f"\n   Columns & Types:")
    for col_name, col_type in zip(frame.columns, frame.schema.values()):
        print(f"      • {col_name}: {col_type}")

    print(f"\n   Sample (first 2 rows):")
    sample = frame.head(2).to_pandas()
    print(sample.to_string(index=False))
    print()


def main() -> None:
    """Inspect all V2 parquet files."""
    files_to_inspect = [
        PROCESSED_DIR / "products_master_v2.parquet",
        PROCESSED_DIR / "product_search_documents_v2.parquet",
        PROCESSED_DIR / "product_embeddings_bge_m3.parquet",
    ]

    print("=" * 80)
    print("🔍 FoodSense V2 Data Inspection")
    print("=" * 80)

    for filepath in files_to_inspect:
        inspect_file(filepath)

    # Quick stats
    print("\n" + "=" * 80)
    print("📊 Quick Stats")
    print("=" * 80)

    for filepath in [PROCESSED_DIR / "products_master_v2.parquet",
                      PROCESSED_DIR / "product_search_documents_v2.parquet"]:
        if filepath.exists():
            frame = pl.read_parquet(filepath)
            name = filepath.name
            # Try to find product ID column
            id_cols = [c for c in frame.columns if "id" in c.lower() or "product" in c.lower()]
            title_cols = [c for c in frame.columns if any(x in c.lower() for x in ["name", "title", "label"])]
            print(f"\n{name}:")
            print(f"  Unique products: {frame.select(id_cols[0]).n_unique() if id_cols else 'N/A'}")
            if title_cols:
                print(f"  Sample names: {frame.select(title_cols[0]).head(3).to_series().to_list()}")


if __name__ == "__main__":
    main()
