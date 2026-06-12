"""Utility functions for evaluating search results against a benchmark of queries and expected relevances."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"

# Prefer product documents files that contain 'v2' in their filename; fall back to any product_documents parquet
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PRODUCT_DOCUMENTS_PATH = None
if PROCESSED_DIR.exists():
    v2_candidates = sorted(PROCESSED_DIR.glob("*product*v2*.parquet"))
    any_candidates = sorted(PROCESSED_DIR.glob("*product*.parquet"))
    if v2_candidates:
        PRODUCT_DOCUMENTS_PATH = v2_candidates[0]
    elif any_candidates:
        PRODUCT_DOCUMENTS_PATH = any_candidates[0]

if PRODUCT_DOCUMENTS_PATH is None:
    PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def load_benchmark() -> list[dict[str, object]]:
    """Load benchmark queries from a JSON file."""
    queries_path = Path(__file__).with_name("queries_test.json")
    return json.loads(queries_path.read_text(encoding="utf-8"))


def load_catalog_texts() -> dict[str, str]:
    """Load product catalog texts from a Parquet file and return a mapping of ProductId to combined text."""
    if not PRODUCT_DOCUMENTS_PATH.exists():
        return {}
    frame = pl.read_parquet(PRODUCT_DOCUMENTS_PATH)

    # Determine the identifier column (support multiple possible names)
    id_candidates = ["ProductId", "product_id", "source_product_id", "sourceProductId"]
    label_candidates = ["label_hint", "title", "name"]
    search_candidates = ["search_text", "search_text_lower", "text", "description"]

    id_col = next((c for c in id_candidates if c in frame.columns), None)
    if id_col is None:
        return {}

    label_col = next((c for c in label_candidates if c in frame.columns), None)
    search_col = next((c for c in search_candidates if c in frame.columns), None)

    select_cols = [id_col]
    if label_col:
        select_cols.append(label_col)
    if search_col:
        select_cols.append(search_col)

    frame = frame.select(select_cols)

    catalog: dict[str, str] = {}
    for row in frame.to_dicts():
        pid = str(row.get(id_col) or "")
        if not pid:
            continue
        label = str(row.get(label_col) or "") if label_col else ""
        search = str(row.get(search_col) or "") if search_col else ""
        combined = f"{label} {search}".strip().lower()
        catalog[pid] = combined
    return catalog


def is_relevant(
    result: dict[str, object],
    benchmark: dict[str, object],
    catalog_texts: dict[str, str],
) -> bool:
    """Determine if a search result is relevant based on the benchmark's positive groups."""
    # Support multiple possible id field names in the result dict
    id_candidates = ["product_id", "ProductId", "productId", "id", "source_product_id", "sourceProductId"]
    product_id = ""
    for c in id_candidates:
        if c in result and result.get(c) is not None:
            product_id = str(result.get(c))
            break

    text = f"{result.get('title') or ''} {catalog_texts.get(product_id, '')}".lower()
    positive_groups = benchmark.get("positive_groups", [])
    if not positive_groups:
        return False
    return all(any(term.lower() in text for term in group) for group in positive_groups)


def score_results(
    benchmark: dict[str, object],
    results: list[dict[str, object]],
    catalog_texts: dict[str, str],
) -> dict[str, object]:
    """Score search results against the benchmark and calculate evaluation metrics."""
    top_k = int(benchmark.get("top_k", len(results) or 1))
    truncated = results[:top_k]
    relevances = [
        1 if is_relevant(result, benchmark, catalog_texts) else 0
        for result in truncated
    ]

    precision_at_k = sum(relevances) / top_k if top_k else 0.0
    success_at_k = 1.0 if any(relevances) else 0.0
    reciprocal_rank = 0.0
    for index, relevance in enumerate(relevances, start=1):
        if relevance:
            reciprocal_rank = 1.0 / index
            break

    return {
        "top_k": top_k,
        "precision_at_k": round(precision_at_k, 4),
        "success_at_k": round(success_at_k, 4),
        "mrr": round(reciprocal_rank, 4),
        "relevances": relevances,
    }


def summarize_metrics(evaluations: list[dict[str, object]]) -> dict[str, object]:
    if not evaluations:
        """If there are no evaluations, return default metrics with zero values and None for average search time."""
        return {
            "queries_total": 0,
            "avg_precision_at_k": 0.0,
            "success_rate_at_k": 0.0,
            "mrr": 0.0,
            "avg_search_time_ms": None,
        }

    precisions = [float(item["metrics"]["precision_at_k"]) for item in evaluations]
    successes = [float(item["metrics"]["success_at_k"]) for item in evaluations]
    mrr_values = [float(item["metrics"]["mrr"]) for item in evaluations]
    search_times = [
        int(item["search_time_ms"])
        for item in evaluations
        if item.get("search_time_ms") is not None
    ]

    return {
        "queries_total": len(evaluations),
        "avg_precision_at_k": round(mean(precisions), 4),
        "success_rate_at_k": round(mean(successes), 4),
        "mrr": round(mean(mrr_values), 4),
        "avg_search_time_ms": round(mean(search_times), 2) if search_times else None,
    }
