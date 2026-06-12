from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
from uuid import NAMESPACE_URL, uuid5

import polars as pl
from qdrant_client.models import Distance, PointStruct, VectorParams

from pipeline.reviews_polars import PROCESSED_DIR
from pipeline.utils.qdrant_client import get_qdrant_client


def iter_points(df: pl.DataFrame) -> Iterable[PointStruct]:
    for row in df.iter_rows(named=True):
        product_id = row["ProductId"]
        payload = {
            "product_id": product_id,
            "label_hint": row.get("label_hint"),
            "review_count": row.get("review_count"),
            "average_score": row.get("average_score"),
            "average_helpfulness_ratio": row.get("average_helpfulness_ratio"),
            "first_review_at": row.get("first_review_at"),
            "last_review_at": row.get("last_review_at"),
            "summary_samples": row.get("summary_samples"),
            "text_samples": row.get("text_samples"),
        }
        yield PointStruct(id=str(uuid5(NAMESPACE_URL, product_id)), vector=row["embedding"], payload=payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index embeddings into Qdrant.")
    parser.add_argument(
        "--embeddings-path",
        default=str(PROCESSED_DIR / "product_embeddings.parquet"),
        help="Path to the embeddings parquet file.",
    )
    parser.add_argument(
        "--collection",
        default="foodsense_products",
        help="Qdrant collection name.",
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
    args = parse_args()
    embeddings_path = Path(args.embeddings_path)

    df = pl.read_parquet(embeddings_path)
    if df.height == 0:
        raise SystemExit("No embeddings found to index.")

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
        points = list(iter_points(batch))
        client.upsert(collection_name=args.collection, points=points)
        indexed += len(points)
        pct = indexed / total * 100
        print(f"{indexed}/{total} ({pct:.1f}%) indexed")

    print("Indexing completed.")


if __name__ == "__main__":
    main()
