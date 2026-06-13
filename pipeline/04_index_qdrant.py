""""Index product embeddings into Qdrant for similarity search.
This script reads product embeddings from a Parquet file, transforms them into the format required by Qdrant, and upserts them into a specified collection. It includes
options for batch size, collection name, and whether to recreate the collection if it already exists.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

import polars as pl
from qdrant_client.models import Distance, PointStruct, VectorParams

from pipeline.reviews_polars import PROCESSED_DIR
from pipeline.utils.qdrant_client import get_qdrant_client


def payload_value(value: Any) -> Any:
    """Convert a value to a JSON-serializable format for Qdrant payloads."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [payload_value(item) for item in value]
    return str(value)


def iter_points(df: pl.DataFrame, id_column: str) -> Iterable[PointStruct]:
    """Yield PointStruct objects for Qdrant upsert from a DataFrame.
    
    Extracts product name from search_text, label_hint, or product_name columns
    and ensures it is always present in the payload for display in search results.
    """
    for row in df.iter_rows(named=True):
        product_id = str(row[id_column])
        payload = {
            key: payload_value(value)
            for key, value in row.items()
            if key != "embedding"
        }
        payload["product_id"] = product_id
        
        # Extract product name from available columns (priority: product_name > label_hint > first line of search_text)
        product_name = None
        if "product_name" in row and row["product_name"]:
            product_name = str(row["product_name"]).strip()
        elif "label_hint" in row and row["label_hint"]:
            product_name = str(row["label_hint"]).strip()
        elif "search_text" in row and row["search_text"]:
            first_line = str(row["search_text"]).split("\n")[0].strip()
            if first_line:
                product_name = first_line
        
        # Ensure product_name is always present (fallback to product_id if needed)
        payload["product_name"] = product_name if product_name else product_id
        
        yield PointStruct(
            id=str(uuid5(NAMESPACE_URL, product_id)),
            vector=row["embedding"],
            payload=payload,
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Index embeddings into Qdrant.")
    
    # Prefer v2 embeddings file if available
    default_embeddings_path = str(PROCESSED_DIR / "product_embeddings.parquet")
    v2_candidates = sorted(PROCESSED_DIR.glob("*embeddings*v2*.parquet"))
    if v2_candidates:
        default_embeddings_path = str(v2_candidates[0])
    
    parser.add_argument(
        "--embeddings-path",
        default=default_embeddings_path,
        help="Path to the embeddings parquet file (prefers v2 if available).",
    )
    parser.add_argument(
        "--collection",
        default="foodsense_products",
        help="Qdrant collection name.",
    )
    parser.add_argument(
        "--id-column",
        default="ProductId",
        help="Column containing the stable product identifier.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection if it already exists.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for upserts.",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to execute the indexing process."""
    args = parse_args()
    embeddings_path = Path(args.embeddings_path)

    df = pl.read_parquet(embeddings_path)
    if df.height == 0:
        raise SystemExit("No embeddings found to index.")
    for required_column in (args.id_column, "embedding"):
        if required_column not in df.columns:
            raise SystemExit(
                f"Missing required column in {embeddings_path}: {required_column}"
            )

    vector_size = len(df["embedding"][0])
    client = get_qdrant_client()
    print("Connected to Qdrant.")

    existing = [c.name for c in client.get_collections().collections]
    if args.collection in existing:
        if args.recreate:
            client.delete_collection(args.collection)
            print(f"Deleted existing collection: {args.collection}")
        else:
            print(f"Collection exists: {args.collection}")

    if args.collection not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"Created collection: {args.collection} (size={vector_size})")

    total = df.height
    batch_size = args.batch_size
    indexed = 0
    for start in range(0, total, batch_size):
        batch = df.slice(start, batch_size)
        points = list(iter_points(batch, args.id_column))
        client.upsert(collection_name=args.collection, points=points)
        indexed += len(points)
        pct = indexed / total * 100
        print(f"{indexed}/{total} ({pct:.1f}%) indexed")

    print("Indexing completed.")


if __name__ == "__main__":
    main()
