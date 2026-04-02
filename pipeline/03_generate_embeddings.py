from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from pipeline.reviews_polars import PROCESSED_DIR


def main() -> None:
    input_path = PROCESSED_DIR / "product_documents.parquet"
    output_path = PROCESSED_DIR / "embedding_manifest.json"

    product_documents = pl.read_parquet(input_path)
    payload = {
        "product_count": product_documents.height,
        "status": "pending-real-embedding-generation",
        "next_step": "Connect Ollama qwen3-embedding:0.6b to batch over search_text.",
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
