from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def load_benchmark() -> list[dict[str, object]]:
    queries_path = Path(__file__).with_name("queries_test.json")
    return json.loads(queries_path.read_text(encoding="utf-8"))


def load_catalog_texts() -> dict[str, str]:
    if not PRODUCT_DOCUMENTS_PATH.exists():
        return {}
    frame = pl.read_parquet(PRODUCT_DOCUMENTS_PATH).select(["ProductId", "label_hint", "search_text"])
    return {
        row["ProductId"]: f"{row.get('label_hint') or ''} {row.get('search_text') or ''}".lower()
        for row in frame.to_dicts()
    }


def is_relevant(result: dict[str, object], benchmark: dict[str, object], catalog_texts: dict[str, str]) -> bool:
    product_id = str(result.get("product_id") or "")
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
    top_k = int(benchmark.get("top_k", len(results) or 1))
    truncated = results[:top_k]
    relevances = [1 if is_relevant(result, benchmark, catalog_texts) else 0 for result in truncated]

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
    search_times = [int(item["search_time_ms"]) for item in evaluations if item.get("search_time_ms") is not None]

    return {
        "queries_total": len(evaluations),
        "avg_precision_at_k": round(mean(precisions), 4),
        "success_rate_at_k": round(mean(successes), 4),
        "mrr": round(mean(mrr_values), 4),
        "avg_search_time_ms": round(mean(search_times), 2) if search_times else None,
    }
