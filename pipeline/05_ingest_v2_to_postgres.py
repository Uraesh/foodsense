"""FoodSense V2 ingestion pipeline: loads USDA, ESCI and Open Food Facts data into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus

import httpx
import polars as pl
import psycopg
from psycopg import sql as pg_sql
from psycopg.types.json import Jsonb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ESCI_PATH = (
    PROJECT_ROOT / "data" / "raw" / "esci" / "shopping_queries_dataset_examples.parquet"
)
USDA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "usda"
    / "FoodData_Central_foundation_food_csv_2026-04-30"
)
OFF_BASE_URL = "https://world.openfoodfacts.org"
SCHEMA = "foodsense_v2"

USDA_KEEP_FILES = {
    "food.csv",
    "foundation_food.csv",
    "food_category.csv",
    "food_nutrient.csv",
    "food_portion.csv",
    "measure_unit.csv",
    "nutrient.csv",
}

ESCI_LABELS = {"E", "S", "C", "I", "Exact", "Substitute", "Complement", "Irrelevant"}
NUTRIENT_AMOUNT_MAX = 1_000_000
PORTION_GRAMS_MAX = 10_000
BATCH_SIZE = 5_000

OFF_NUTRIMENT_COLS: list[str] = [
    "energy-kcal_100g",
    "energy_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "fiber_100g",
    "proteins_100g",
    "salt_100g",
    "sodium_100g",
]


SCHEMA_SQL = f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA};

CREATE TABLE IF NOT EXISTS {SCHEMA}.ingestion_runs (
    run_id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    notes JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.openfoodfacts_products (
    code TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    brand TEXT,
    categories TEXT,
    ingredients_text TEXT,
    allergens TEXT,
    nutriscore TEXT,
    nutriments JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    source_url TEXT,
    raw_payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.products_master (
    product_id TEXT PRIMARY KEY,
    barcode TEXT,
    product_name TEXT NOT NULL,
    brand TEXT,
    categories TEXT,
    ingredients_text TEXT,
    allergens TEXT,
    nutrition_summary TEXT,
    nutriscore TEXT,
    source_dataset TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.product_search_documents (
    source_product_id TEXT PRIMARY KEY,
    source_dataset TEXT NOT NULL,
    search_text TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_food_categories (
    id INTEGER PRIMARY KEY,
    code TEXT,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_foods (
    fdc_id INTEGER PRIMARY KEY,
    data_type TEXT,
    description TEXT NOT NULL,
    food_category_id INTEGER,
    food_category TEXT,
    publication_date TEXT
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_foundation_foods (
    fdc_id INTEGER PRIMARY KEY,
    ndb_number TEXT,
    footnote TEXT
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_nutrients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    nutrient_nbr TEXT,
    unit_name TEXT,
    rank INTEGER
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_food_nutrients (
    id INTEGER PRIMARY KEY,
    fdc_id INTEGER NOT NULL,
    nutrient_id INTEGER NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    data_points INTEGER,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    median_value DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_usda_food_nutrients_fdc
ON {SCHEMA}.usda_food_nutrients (fdc_id);

CREATE INDEX IF NOT EXISTS idx_usda_food_nutrients_nutrient
ON {SCHEMA}.usda_food_nutrients (nutrient_id);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_measure_units (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.usda_food_portions (
    id INTEGER PRIMARY KEY,
    fdc_id INTEGER NOT NULL,
    measure_unit_id INTEGER,
    measure_unit TEXT,
    amount DOUBLE PRECISION,
    gram_weight DOUBLE PRECISION NOT NULL,
    portion_description TEXT,
    modifier TEXT
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.esci_examples (
    example_id BIGINT PRIMARY KEY,
    query TEXT NOT NULL,
    query_id BIGINT NOT NULL,
    product_id TEXT NOT NULL,
    product_locale TEXT,
    esci_label TEXT NOT NULL,
    split TEXT,
    small_version INTEGER,
    large_version INTEGER
);

CREATE INDEX IF NOT EXISTS idx_esci_query_id
ON {SCHEMA}.esci_examples (query_id);

CREATE INDEX IF NOT EXISTS idx_esci_product_id
ON {SCHEMA}.esci_examples (product_id);
"""


def clean_text_expr(name: str) -> pl.Expr:
    """Return a Polars expression that strips and normalises whitespace for a column."""
    return (
        pl.col(name)
        .cast(pl.Utf8, strict=False)
        .str.strip_chars()
        .str.replace_all(r"\s+", " ")
    )


def database_url_from_env() -> str:
    """Build the PostgreSQL connection URL from environment variables."""
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


def load_env_defaults() -> None:
    """Populate missing environment variables from .env.example then .env."""
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


def connect() -> psycopg.Connection:  # type: ignore[type-arg]
    """Load env defaults and return an open PostgreSQL connection."""
    load_env_defaults()
    return psycopg.connect(database_url_from_env())


def chunks(
    values: list[tuple[Any, ...]], size: int = BATCH_SIZE
) -> Iterable[list[tuple[Any, ...]]]:
    """Yield successive batches of `size` rows from `values`."""
    for start in range(0, len(values), size):
        yield values[start : start + size]


def upsert_rows(
    conn: psycopg.Connection,  # type: ignore[type-arg]
    table: str,
    columns: list[str],
    rows: list[tuple[Any, ...]],
    conflict_columns: list[str],
) -> int:
    """Upsert rows into a table, updating on conflict or doing nothing."""
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    conflict_sql = ", ".join(conflict_columns)
    update_columns = [col for col in columns if col not in conflict_columns]
    if update_columns:
        update_sql = ", ".join(f"{col}=EXCLUDED.{col}" for col in update_columns)
        conflict_action = f"DO UPDATE SET {update_sql}"
    else:
        conflict_action = "DO NOTHING"
    query = pg_sql.SQL(
        f"INSERT INTO {SCHEMA}.{table} ({column_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_sql}) {conflict_action}"
    )
    with conn.cursor() as cur:
        for batch in chunks(rows):
            cur.executemany(query, batch)
    return len(rows)


def create_schema(conn: psycopg.Connection) -> None:  # type: ignore[type-arg]
    """Create all FoodSense V2 tables and indexes if they do not yet exist."""
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()


def start_run(
    conn: psycopg.Connection,  # type: ignore[type-arg]
    source: str,
    notes: dict[str, Any] | None = None,
) -> uuid.UUID:
    """Insert a new ingestion_runs record with status 'running' and return its UUID."""
    run_id = uuid.uuid4()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {SCHEMA}.ingestion_runs (run_id, source, status, notes)
            VALUES (%s, %s, 'running', %s)
            """,
            (run_id, source, Jsonb(notes or {})),
        )
    conn.commit()
    return run_id


def finish_run(
    conn: psycopg.Connection,  # type: ignore[type-arg]
    run_id: uuid.UUID,
    status: str,
    row_count: int,
    notes: dict[str, Any] | None = None,
) -> None:
    """Update an ingestion_runs record with its final status, row count and notes."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE {SCHEMA}.ingestion_runs
            SET status=%s, row_count=%s, notes=%s, finished_at=now()
            WHERE run_id=%s
            """,
            (status, row_count, Jsonb(notes or {}), run_id),
        )
    conn.commit()


def read_csv(name: str) -> pl.DataFrame:
    """Read a USDA CSV file from the configured directory into a Polars DataFrame."""
    path = USDA_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pl.read_csv(path, infer_schema_length=10_000, ignore_errors=True)


def import_usda(conn: psycopg.Connection) -> dict[str, int]:  # type: ignore[type-arg]
    """Import all USDA Foundation Food CSV files and return per-table row counts."""
    run_id = start_run(conn, "usda_foundation_food", {"directory": str(USDA_DIR)})
    counts: dict[str, int] = {}
    try:
        categories = (
            read_csv("food_category.csv")
            .select(
                pl.col("id").cast(pl.Int64, strict=False),
                clean_text_expr("code").alias("code"),
                clean_text_expr("description").alias("description"),
            )
            .filter(pl.col("id").is_not_null() & (pl.col("description") != ""))
            .unique(subset=["id"], keep="first")
        )
        cols_categories = ["id", "code", "description"]
        counts["usda_food_categories"] = upsert_rows(
            conn,
            "usda_food_categories",
            cols_categories,
            list(categories.select(cols_categories).iter_rows()),
            ["id"],
        )

        foods = (
            read_csv("food.csv")
            .select(
                pl.col("fdc_id").cast(pl.Int64, strict=False),
                clean_text_expr("data_type").alias("data_type"),
                clean_text_expr("description").alias("description"),
                pl.col("food_category_id").cast(pl.Int64, strict=False),
                clean_text_expr("publication_date").alias("publication_date"),
            )
            .filter(pl.col("fdc_id").is_not_null() & (pl.col("description") != ""))
            .unique(subset=["fdc_id"], keep="first")
            .join(
                categories.select(
                    pl.col("id").alias("food_category_id"),
                    pl.col("description").alias("food_category"),
                ),
                on="food_category_id",
                how="left",
            )
        )
        cols_foods = [
            "fdc_id",
            "data_type",
            "description",
            "food_category_id",
            "food_category",
            "publication_date",
        ]
        counts["usda_foods"] = upsert_rows(
            conn,
            "usda_foods",
            cols_foods,
            list(foods.select(cols_foods).iter_rows()),
            ["fdc_id"],
        )

        foundation = (
            read_csv("foundation_food.csv")
            .select(
                pl.col("fdc_id").cast(pl.Int64, strict=False),
                clean_text_expr("NDB_number").alias("ndb_number"),
                clean_text_expr("footnote").alias("footnote"),
            )
            .filter(pl.col("fdc_id").is_not_null())
            .unique(subset=["fdc_id"], keep="first")
        )
        cols_foundation = ["fdc_id", "ndb_number", "footnote"]
        counts["usda_foundation_foods"] = upsert_rows(
            conn,
            "usda_foundation_foods",
            cols_foundation,
            list(foundation.select(cols_foundation).iter_rows()),
            ["fdc_id"],
        )

        nutrients = (
            read_csv("nutrient.csv")
            .select(
                pl.col("id").cast(pl.Int64, strict=False),
                clean_text_expr("name").alias("name"),
                clean_text_expr("nutrient_nbr").alias("nutrient_nbr"),
                clean_text_expr("unit_name").alias("unit_name"),
                pl.col("rank").cast(pl.Int64, strict=False),
            )
            .filter(pl.col("id").is_not_null() & (pl.col("name") != ""))
            .unique(subset=["id"], keep="first")
        )
        cols_nutrients = ["id", "name", "nutrient_nbr", "unit_name", "rank"]
        counts["usda_nutrients"] = upsert_rows(
            conn,
            "usda_nutrients",
            cols_nutrients,
            list(nutrients.select(cols_nutrients).iter_rows()),
            ["id"],
        )

        food_nutrients = (
            read_csv("food_nutrient.csv")
            .select(
                pl.col("id").cast(pl.Int64, strict=False),
                pl.col("fdc_id").cast(pl.Int64, strict=False),
                pl.col("nutrient_id").cast(pl.Int64, strict=False),
                pl.col("amount").cast(pl.Float64, strict=False),
                pl.col("data_points").cast(pl.Int64, strict=False),
                pl.col("min").cast(pl.Float64, strict=False).alias("min_value"),
                pl.col("max").cast(pl.Float64, strict=False).alias("max_value"),
                pl.col("median").cast(pl.Float64, strict=False).alias("median_value"),
            )
            .filter(
                pl.col("id").is_not_null()
                & pl.col("fdc_id").is_not_null()
                & pl.col("nutrient_id").is_not_null()
                & pl.col("amount").is_not_null()
                & (pl.col("amount") >= 0)
                & (pl.col("amount") <= NUTRIENT_AMOUNT_MAX)
            )
            .unique(subset=["id"], keep="first")
        )
        cols_food_nutrients = [
            "id",
            "fdc_id",
            "nutrient_id",
            "amount",
            "data_points",
            "min_value",
            "max_value",
            "median_value",
        ]
        counts["usda_food_nutrients"] = upsert_rows(
            conn,
            "usda_food_nutrients",
            cols_food_nutrients,
            list(food_nutrients.select(cols_food_nutrients).iter_rows()),
            ["id"],
        )

        units = (
            read_csv("measure_unit.csv")
            .select(
                pl.col("id").cast(pl.Int64, strict=False),
                clean_text_expr("name").alias("name"),
            )
            .filter(pl.col("id").is_not_null() & (pl.col("name") != ""))
            .unique(subset=["id"], keep="first")
        )
        cols_units = ["id", "name"]
        counts["usda_measure_units"] = upsert_rows(
            conn,
            "usda_measure_units",
            cols_units,
            list(units.select(cols_units).iter_rows()),
            ["id"],
        )

        portions = (
            read_csv("food_portion.csv")
            .select(
                pl.col("id").cast(pl.Int64, strict=False),
                pl.col("fdc_id").cast(pl.Int64, strict=False),
                pl.col("measure_unit_id").cast(pl.Int64, strict=False),
                pl.col("amount").cast(pl.Float64, strict=False),
                pl.col("gram_weight").cast(pl.Float64, strict=False),
                clean_text_expr("portion_description").alias("portion_description"),
                clean_text_expr("modifier").alias("modifier"),
            )
            .filter(
                pl.col("id").is_not_null()
                & pl.col("fdc_id").is_not_null()
                & pl.col("gram_weight").is_not_null()
                & (pl.col("gram_weight") > 0)
                & (pl.col("gram_weight") <= PORTION_GRAMS_MAX)
            )
            .unique(subset=["id"], keep="first")
            .join(
                units.select(
                    pl.col("id").alias("measure_unit_id"),
                    pl.col("name").alias("measure_unit"),
                ),
                on="measure_unit_id",
                how="left",
            )
        )
        cols_portions = [
            "id",
            "fdc_id",
            "measure_unit_id",
            "measure_unit",
            "amount",
            "gram_weight",
            "portion_description",
            "modifier",
        ]
        counts["usda_food_portions"] = upsert_rows(
            conn,
            "usda_food_portions",
            cols_portions,
            list(portions.select(cols_portions).iter_rows()),
            ["id"],
        )

        conn.commit()
        finish_run(conn, run_id, "succeeded", sum(counts.values()), counts)
        return counts
    except Exception as exc:
        conn.rollback()
        finish_run(conn, run_id, "failed", 0, {"error": str(exc)})
        raise


def import_esci(conn: psycopg.Connection, path: Path = ESCI_PATH) -> int:  # type: ignore[type-arg]
    """Import ESCI query-product relevance examples from a parquet file."""
    run_id = start_run(conn, "esci_examples", {"path": str(path)})
    try:
        if not path.exists():
            raise FileNotFoundError(path)
        df = (
            pl.read_parquet(path)
            .select(
                pl.col("example_id").cast(pl.Int64, strict=False),
                clean_text_expr("query").alias("query"),
                pl.col("query_id").cast(pl.Int64, strict=False),
                clean_text_expr("product_id").alias("product_id"),
                clean_text_expr("product_locale").alias("product_locale"),
                clean_text_expr("esci_label").alias("esci_label"),
                clean_text_expr("split").alias("split"),
                pl.col("small_version").cast(pl.Int64, strict=False),
                pl.col("large_version").cast(pl.Int64, strict=False),
            )
            .filter(
                pl.col("example_id").is_not_null()
                & pl.col("query_id").is_not_null()
                & (pl.col("query") != "")
                & (pl.col("product_id") != "")
                & pl.col("esci_label").is_in(sorted(ESCI_LABELS))
            )
            .unique(subset=["example_id"], keep="first")
        )
        cols_esci = [
            "example_id",
            "query",
            "query_id",
            "product_id",
            "product_locale",
            "esci_label",
            "split",
            "small_version",
            "large_version",
        ]
        count = upsert_rows(
            conn,
            "esci_examples",
            cols_esci,
            list(df.select(cols_esci).iter_rows()),
            ["example_id"],
        )
        conn.commit()
        finish_run(conn, run_id, "succeeded", count, {"rows": count})
        return count
    except Exception as exc:
        conn.rollback()
        finish_run(conn, run_id, "failed", 0, {"error": str(exc)})
        raise


def best_text(product: dict[str, Any], *keys: str) -> str:
    """Return the first non-empty string found under any of the given keys in product."""
    for key in keys:
        value = product.get(key)
        if isinstance(value, str) and value.strip():
            return re.sub(r"\s+", " ", value.strip())
    return ""


def normalize_off_product(
    payload: dict[str, Any], barcode: str
) -> tuple[Any, ...] | None:
    """Extract and normalise a single OFF API payload into a DB-ready row tuple."""
    product: dict[str, Any] = payload.get("product") or {}
    code = str(payload.get("code") or product.get("code") or barcode).strip()
    product_name = best_text(
        product,
        "product_name",
        "product_name_en",
        "product_name_fr",
        "generic_name",
        "generic_name_en",
        "generic_name_fr",
    )
    if not code or not product_name:
        return None
    brand = best_text(product, "brands")
    categories = best_text(product, "categories")
    ingredients = best_text(
        product,
        "ingredients_text",
        "ingredients_text_en",
        "ingredients_text_fr",
    )
    allergens = best_text(product, "allergens")
    nutriscore = best_text(product, "nutriscore_grade", "nutriscore_score")
    nutriments_raw = product.get("nutriments")
    nutriments: dict[str, Any] = (
        nutriments_raw if isinstance(nutriments_raw, dict) else {}
    )
    source_url = f"{OFF_BASE_URL}/product/{code}"
    return (
        code,
        product_name,
        brand,
        categories,
        ingredients,
        allergens,
        nutriscore,
        Jsonb(nutriments),
        source_url,
        Jsonb(payload),
    )


def load_barcodes(values: list[str], barcode_file: Path | None) -> list[str]:
    """Collect, deduplicate and sort barcodes from CLI values and an optional file."""
    barcodes: list[str] = []
    for value in values:
        barcodes.extend(part.strip() for part in value.split(",") if part.strip())
    if barcode_file:
        lines = barcode_file.read_text(encoding="utf-8").splitlines()
        barcodes.extend(
            line.strip() for line in lines if line.strip() and not line.startswith("#")
        )
    return sorted(set(barcodes))


def fetch_off_product(client: httpx.Client, barcode: str) -> dict[str, Any]:
    """Fetch a product JSON payload from the Open Food Facts API v3.6 by barcode."""
    url = f"{OFF_BASE_URL}/api/v3.6/product/{barcode}.json"
    response = client.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()


def import_openfoodfacts(
    conn: psycopg.Connection,  # type: ignore[type-arg]
    barcodes: list[str],
    basic_auth: str | None = None,
) -> int:
    """Fetch OFF products by barcode via the API and upsert them into PostgreSQL."""
    if not barcodes:
        return 0
    run_id = start_run(conn, "openfoodfacts_api", {"barcodes": len(barcodes)})
    rows: list[tuple[Any, ...]] = []
    headers = {"User-Agent": "FoodSense-V2-MVP/0.1"}
    auth_pair: tuple[str, str] | None = None
    if basic_auth and ":" in basic_auth:
        left, right = basic_auth.split(":", 1)
        auth_pair = (left, right)
    try:
        with httpx.Client(
            headers=headers, auth=auth_pair, follow_redirects=True
        ) as client:
            for barcode in barcodes:
                payload = fetch_off_product(client, barcode)
                row = normalize_off_product(payload, barcode)
                if row:
                    rows.append(row)
        count = upsert_rows(
            conn,
            "openfoodfacts_products",
            [
                "code",
                "product_name",
                "brand",
                "categories",
                "ingredients_text",
                "allergens",
                "nutriscore",
                "nutriments",
                "source_url",
                "raw_payload",
            ],
            rows,
            ["code"],
        )
        rebuild_products_master(conn)
        conn.commit()
        finish_run(
            conn,
            run_id,
            "succeeded",
            count,
            {"accepted": count, "requested": len(barcodes)},
        )
        return count
    except Exception as exc:
        conn.rollback()
        finish_run(conn, run_id, "failed", 0, {"error": str(exc)})
        raise


def import_off_csv(
    conn: psycopg.Connection,  # type: ignore[type-arg]
    csv_path: Path,
    limit: int = 10_000,
) -> int:
    """Read an OFF CSV dump file, take `limit` clean rows and upsert into PostgreSQL."""
    run_id = start_run(
        conn,
        "openfoodfacts_csv",
        {"path": str(csv_path), "limit": limit},
    )
    try:
        oversample = min(limit * 5, 500_000)
        df = pl.read_csv(
            csv_path,
            separator="\t",
            n_rows=oversample,
            infer_schema_length=0,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )

        available_nutriments = [c for c in OFF_NUTRIMENT_COLS if c in df.columns]

        if "code" not in df.columns or "product_name" not in df.columns:
            raise ValueError("OFF CSV missing required columns: code, product_name")

        # Colonnes optionnelles a normaliser si elles existent
        optional_str_cols = [
            c
            for c in [
                "brands",
                "categories",
                "ingredients_text",
                "allergens",
                "nutriscore_grade",
                "url",
            ]
            if c in df.columns
        ]

        df = (
            df.with_columns(
                [
                    pl.col("code").str.strip_chars(),
                    pl.col("product_name").str.strip_chars(),
                ]
                + [pl.col(c).str.strip_chars() for c in optional_str_cols]
            )
            # 1. code et product_name obligatoires
            .filter(
                pl.col("code").is_not_null()
                & (pl.col("code") != "")
                & pl.col("product_name").is_not_null()
                & (pl.col("product_name") != "")
            )
            # 2. code EAN valide : uniquement des chiffres, longueur 8 ou 13
            .filter(
                pl.col("code").str.contains(r"^\d{8}$")
                | pl.col("code").str.contains(r"^\d{13}$")
            )
            # 3. product_name pas trop court (evite les donnees poubelles)
            .filter(pl.col("product_name").str.len_chars() >= 3)
            # 4. au moins un champ utile renseigne parmi categories / ingredients / nutriscore
            .filter(
                (
                    pl.col("categories").is_not_null() & (pl.col("categories") != "")
                    if "categories" in df.columns
                    else pl.lit(False)
                )
                | (
                    pl.col("ingredients_text").is_not_null()
                    & (pl.col("ingredients_text") != "")
                    if "ingredients_text" in df.columns
                    else pl.lit(False)
                )
                | (
                    pl.col("nutriscore_grade").is_not_null()
                    & (pl.col("nutriscore_grade").str.contains(r"^[abcde]$"))
                    if "nutriscore_grade" in df.columns
                    else pl.lit(False)
                )
            )
            # 5. deduplication sur le code-barres
            .unique(subset=["code"])
            .head(limit)
        )

        rows: list[tuple[Any, ...]] = []
        for record in df.to_dicts():
            code = (record.get("code") or "").strip()
            product_name = (record.get("product_name") or "").strip()
            if not code or not product_name:
                continue

            brand = (record.get("brands") or "").strip()
            categories_raw = (record.get("categories") or "").strip()
            ingredients = (record.get("ingredients_text") or "").strip()
            allergens = (record.get("allergens") or "").strip()
            nutriscore = (record.get("nutriscore_grade") or "").strip().lower()

            # Nettoyage : supprimer les prefixes de langue (fr:, en:, de:...)
            # et normaliser les separateurs
            def clean_field(val: str) -> str:
                val = re.sub(r"\b[a-z]{2}:", "", val)  # fr:, en:, de:...
                val = val.replace(";", ",")  # ; -> ,
                val = re.sub(r",\s*,", ",", val)  # doubles virgules
                val = re.sub(r"\s+", " ", val).strip(" ,")
                return val if val.lower() not in ("unknown", "n/a", "-", "") else ""

            # Nettoyer le product_name (pas de ; ni prefixes)
            product_name = re.sub(r"\s+", " ", product_name.replace(";", " ")).strip()
            if not product_name or product_name.lower() in ("unknown", "n/a", "-"):
                continue

            brand = clean_field(brand)
            categories = clean_field(categories_raw)
            allergens = clean_field(allergens)
            # Nutriscore : uniquement a b c d e
            nutriscore = nutriscore if nutriscore in ("a", "b", "c", "d", "e") else ""

            nutriments: dict[str, Any] = {}
            for col in available_nutriments:
                raw_val = record.get(col)
                if raw_val not in (None, "", "nan"):
                    try:
                        nutriments[col] = float(raw_val)  # type: ignore[arg-type]
                    except (ValueError, TypeError):
                        pass

            source_url = record.get("url") or f"{OFF_BASE_URL}/product/{code}"
            raw_payload: dict[str, Any] = {
                "code": code,
                "product_name": product_name,
                "brands": brand,
                "categories": categories,
                "nutriscore_grade": nutriscore,
                **nutriments,
            }

            rows.append(
                (
                    code,
                    product_name,
                    brand,
                    categories,
                    ingredients,
                    allergens,
                    nutriscore,
                    Jsonb(nutriments),
                    source_url,
                    Jsonb(raw_payload),
                )
            )

        count = upsert_rows(
            conn,
            "openfoodfacts_products",
            [
                "code",
                "product_name",
                "brand",
                "categories",
                "ingredients_text",
                "allergens",
                "nutriscore",
                "nutriments",
                "source_url",
                "raw_payload",
            ],
            rows,
            ["code"],
        )
        rebuild_products_master(conn)
        conn.commit()
        finish_run(conn, run_id, "succeeded", count, {"ingested": count})
        return count
    except Exception as exc:
        conn.rollback()
        finish_run(conn, run_id, "failed", 0, {"error": str(exc)})
        raise


def rebuild_products_master(conn: psycopg.Connection) -> None:  # type: ignore[type-arg]
    """Upsert OFF et USDA rows dans products_master et product_search_documents."""
    with conn.cursor() as cur:
        # ── 1. Open Food Facts ──────────────────────────────────────────────
        cur.execute(
            f"""
            INSERT INTO {SCHEMA}.products_master (
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
                payload
            )
            SELECT
                'off:' || code,
                code,
                product_name,
                brand,
                categories,
                ingredients_text,
                allergens,
                concat_ws(
                    ' ',
                    nullif(nutriments->>'energy-kcal_100g', ''),
                    nullif(nutriments->>'proteins_100g', ''),
                    nullif(nutriments->>'fat_100g', ''),
                    nullif(nutriments->>'sugars_100g', ''),
                    nullif(nutriments->>'salt_100g', '')
                ),
                nutriscore,
                'openfoodfacts',
                raw_payload
            FROM {SCHEMA}.openfoodfacts_products
            WHERE product_name IS NOT NULL
              AND length(trim(product_name)) > 1
            ON CONFLICT (product_id) DO UPDATE SET
                barcode          = EXCLUDED.barcode,
                product_name     = EXCLUDED.product_name,
                brand            = EXCLUDED.brand,
                categories       = EXCLUDED.categories,
                ingredients_text = EXCLUDED.ingredients_text,
                allergens        = EXCLUDED.allergens,
                nutrition_summary= EXCLUDED.nutrition_summary,
                nutriscore       = EXCLUDED.nutriscore,
                payload          = EXCLUDED.payload,
                updated_at       = now()
            """
        )

        # ── 2. USDA Foundation Foods ────────────────────────────────────────
        cur.execute(
            f"""
            INSERT INTO {SCHEMA}.products_master (
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
                payload
            )
            SELECT
                'usda:' || f.fdc_id::text,
                f.fdc_id::text,
                initcap(lower(f.description)),
                'USDA Foundation Foods',
                fc.description,
                NULL,
                NULL,
                concat_ws(
                    ' | ',
                    'Energy: ' || fn_energy.amount::text || ' kcal',
                    'Protein: ' || fn_prot.amount::text || ' g',
                    'Fat: '    || fn_fat.amount::text   || ' g'
                ),
                NULL,
                'usda',
                jsonb_build_object(
                    'fdc_id',      f.fdc_id,
                    'description', f.description,
                    'category',    fc.description
                )
            FROM {SCHEMA}.usda_foods f
            LEFT JOIN {SCHEMA}.usda_food_categories fc
                   ON f.food_category_id = fc.id
            LEFT JOIN {SCHEMA}.usda_food_nutrients fn_energy
                   ON fn_energy.fdc_id = f.fdc_id
                  AND fn_energy.nutrient_id = 1008   -- Energy kcal
            LEFT JOIN {SCHEMA}.usda_food_nutrients fn_prot
                   ON fn_prot.fdc_id = f.fdc_id
                  AND fn_prot.nutrient_id = 1003     -- Protein
            LEFT JOIN {SCHEMA}.usda_food_nutrients fn_fat
                   ON fn_fat.fdc_id = f.fdc_id
                  AND fn_fat.nutrient_id = 1004      -- Total fat
            WHERE f.description IS NOT NULL
              AND length(trim(f.description)) > 1
            ON CONFLICT (product_id) DO UPDATE SET
                product_name     = EXCLUDED.product_name,
                categories       = EXCLUDED.categories,
                nutrition_summary= EXCLUDED.nutrition_summary,
                payload          = EXCLUDED.payload,
                updated_at       = now()
            """
        )

        # ── 3. product_search_documents (OFF + USDA) ────────────────────────
        # search_text : langage naturel uniquement, pas de chiffres bruts
        cur.execute(
            f"""
            INSERT INTO {SCHEMA}.product_search_documents (
                source_product_id,
                source_dataset,
                search_text,
                payload
            )
            SELECT
                product_id,
                source_dataset,
                trim(concat_ws(
                    ' ',
                    nullif(trim(product_name), ''),
                    nullif(trim(brand), ''),
                    nullif(trim(categories), ''),
                    nullif(left(trim(ingredients_text), 400), ''),
                    nullif(trim(allergens), ''),
                    CASE
                        WHEN nutriscore IN ('a','b','c','d','e')
                        THEN 'Nutri-Score ' || upper(nutriscore)
                        ELSE NULL
                    END
                )),
                payload
            FROM {SCHEMA}.products_master
            WHERE product_name IS NOT NULL
              AND length(trim(product_name)) > 1
            ON CONFLICT (source_product_id) DO UPDATE SET
                source_dataset = EXCLUDED.source_dataset,
                search_text    = EXCLUDED.search_text,
                payload        = EXCLUDED.payload,
                updated_at     = now()
            """
        )


def print_usda_keep_files() -> None:
    """Print the USDA CSV files retained for the MVP."""
    print("USDA CSV kept for MVP:")
    for name in sorted(USDA_KEEP_FILES):
        print(f"- {name}")


def main() -> None:
    """Parse CLI arguments and run the requested ingestion steps."""
    parser = argparse.ArgumentParser(
        description="Import FoodSense V2 datasets into PostgreSQL."
    )
    parser.add_argument(
        "--skip-usda", action="store_true", help="Skip USDA Foundation Food CSV import."
    )
    parser.add_argument(
        "--skip-esci", action="store_true", help="Skip ESCI parquet import."
    )
    parser.add_argument(
        "--skip-off", action="store_true", help="Skip Open Food Facts API import."
    )
    parser.add_argument(
        "--off-barcode",
        action="append",
        default=[],
        help="Open Food Facts barcode; comma-separated values accepted.",
    )
    parser.add_argument(
        "--off-barcode-file",
        type=Path,
        help="Text file containing one Open Food Facts barcode per line.",
    )
    parser.add_argument(
        "--off-basic-auth",
        help="Optional basic auth pair, e.g. off:off on test servers.",
    )
    parser.add_argument(
        "--print-usda-keep-files",
        action="store_true",
        help="Print the USDA files selected for the MVP.",
    )
    parser.add_argument(
        "--off-csv",
        type=Path,
        help="Path to an OFF CSV dump file (.csv or .csv.gz) for bulk import.",
    )
    parser.add_argument(
        "--off-limit",
        type=int,
        default=10_000,
        help="Max rows to import from --off-csv (default: 10000).",
    )
    args = parser.parse_args()

    if args.print_usda_keep_files:
        print_usda_keep_files()

    barcodes = load_barcodes(args.off_barcode, args.off_barcode_file)

    off_will_run = not args.skip_off and (args.off_csv or barcodes)
    if args.skip_usda and args.skip_esci and not off_will_run:
        return

    with connect() as conn:
        create_schema(conn)
        if not args.skip_usda:
            counts = import_usda(conn)
            print(json.dumps({"usda": counts}, indent=2, sort_keys=True))
        if not args.skip_esci:
            count = import_esci(conn)
            print(json.dumps({"esci_examples": count}, indent=2, sort_keys=True))
        if not args.skip_off:
            if args.off_csv:
                count = import_off_csv(conn, args.off_csv, args.off_limit)
                print(
                    json.dumps({"openfoodfacts_csv": count}, indent=2, sort_keys=True)
                )
            elif barcodes:
                count = import_openfoodfacts(conn, barcodes, args.off_basic_auth)
                print(
                    json.dumps(
                        {"openfoodfacts_products": count}, indent=2, sort_keys=True
                    )
                )
            else:
                print(
                    "Open Food Facts skipped: provide --off-csv, "
                    "--off-barcode or --off-barcode-file."
                )


if __name__ == "__main__":
    main()
