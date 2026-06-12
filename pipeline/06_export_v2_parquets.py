"""Export processed FoodSense V2 data from PostgreSQL to Parquet files.
This script connects to the PostgreSQL database, reads the products_master and product_search_documents tables, performs quality checks, and exports the data to Parquet files. It also generates a quality report in JSON format summarizing the checks performed on the data.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote_plus

import polars as pl
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA = "foodsense_v2"


def load_env_defaults() -> None:
    """Load environment variables from .env files if not already set in the environment."""
    for env_path in (PROJECT_ROOT / ".env.example", PROJECT_ROOT / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def database_url_from_env() -> str:
    """Construct the database URL from environment variables or a single DATABASE_URL variable."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "Foodsense")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD")
    if not password:
        raise RuntimeError(
            "Missing PostgreSQL password. Set POSTGRES_PASSWORD or DATABASE_URL."
        )
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{quote_plus(database)}"
    )


def connect() -> psycopg.Connection:
    """Establish a connection to the PostgreSQL database using credentials from environment variables."""
    load_env_defaults()
    return psycopg.connect(database_url_from_env())


def read_query(conn: psycopg.Connection, query: str) -> pl.DataFrame:
    """Execute a SQL query and return the results as a Polars DataFrame."""
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc.name for desc in cur.description or []]
    return pl.DataFrame(rows, schema=columns, orient="row")


def assert_quality(
    products: pl.DataFrame, documents: pl.DataFrame
) -> dict[str, object]:
    """Perform quality checks on the products and documents DataFrames and return a report."""
    product_duplicates = products.select(pl.col("product_id").n_unique()).item()
    document_duplicates = documents.select(pl.col("product_id").n_unique()).item()
    blank_names = products.filter(pl.col("product_name").str.strip_chars() == "").height
    blank_search_text = documents.filter(
        pl.col("search_text").str.strip_chars() == ""
    ).height

    report = {
        "products_rows": products.height,
        "products_unique_ids": product_duplicates,
        "documents_rows": documents.height,
        "documents_unique_ids": document_duplicates,
        "blank_product_names": blank_names,
        "blank_search_text": blank_search_text,
        "status": "passed",
    }

    failures: list[str] = []
    if products.height == 0:
        failures.append("products_master is empty")
    if documents.height == 0:
        failures.append("product_search_documents is empty")
    if product_duplicates != products.height:
        failures.append("products_master contains duplicate product_id values")
    if document_duplicates != documents.height:
        failures.append("product_search_documents contains duplicate product_id values")
    if blank_names > 0:
        failures.append("products_master contains blank product_name values")
    if blank_search_text > 0:
        failures.append("product_search_documents contains blank search_text values")

    if failures:
        report["status"] = "failed"
        report["failures"] = failures
        raise RuntimeError(json.dumps(report, indent=2))

    return report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export FoodSense V2 PostgreSQL tables to parquet artifacts."
    )
    parser.add_argument(
        "--products-path",
        type=Path,
        default=PROCESSED_DIR / "products_master_v2.parquet",
    )
    parser.add_argument(
        "--documents-path",
        type=Path,
        default=PROCESSED_DIR / "product_search_documents_v2.parquet",
    )
    parser.add_argument(
        "--quality-report-path",
        type=Path,
        default=PROCESSED_DIR / "quality_report_v2.json",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to execute the export process."""
    args = parse_args()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with connect() as conn:
        products = read_query(
            conn,
            f"""
            SELECT
                product_id,
                barcode,
                product_name,
                brand,
                categories,
                ingredients_text,
                allergens,
                nutrition_summary,
                nutriscore,
                source_dataset,
                payload::text AS payload_json,
                updated_at::text AS updated_at
            FROM {SCHEMA}.products_master
            ORDER BY product_id
            """,
        )
        documents = read_query(
            conn,
            f"""
            SELECT
                source_product_id AS product_id,
                source_dataset,
                search_text,
                payload::text AS payload_json,
                updated_at::text AS updated_at
            FROM {SCHEMA}.product_search_documents
            ORDER BY source_product_id
            """,
        )

    report = assert_quality(products, documents)
    products.write_parquet(args.products_path)
    documents.write_parquet(args.documents_path)
    args.quality_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {args.products_path}")
    print(f"Wrote {args.documents_path}")
    print(f"Wrote {args.quality_report_path}")


if __name__ == "__main__":
    main()
