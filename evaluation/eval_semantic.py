"""Evaluate the semantic search API using a benchmark of queries and expected results."""
from __future__ import annotations

import json
import sys
import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  
from app.services.embedding_service import warmup_embedding_model
from eval_utils import (
    load_benchmark,
    load_catalog_texts,
    score_results,
    summarize_metrics,
)


def main() -> None:
    """Main function to run the semantic search evaluation."""
    report_path = Path(__file__).with_name("semantic_eval_report.json")
    benchmark = load_benchmark()
    catalog_texts = load_catalog_texts()

    client = TestClient(app)
    evaluations: list[dict[str, object]] = []
    asyncio.run(warmup_embedding_model())

    for item in benchmark:
        query = str(item["query"])
        top_k = int(item.get("top_k", 5))
        response = client.get("/search", params={"query": query, "top_k": top_k})
        payload = response.json()
        results = payload.get("results", [])
        metrics = score_results(item, results, catalog_texts)
        evaluations.append(
            {
                "query": query,
                "top_k": top_k,
                "status_code": response.status_code,
                "strategy": payload.get("strategy"),
                "warning": payload.get("warning"),
                "search_time_ms": payload.get("search_time_ms"),
                "metrics": metrics,
                "top_results": [
                    {
                        **result,
                        "relevant": bool(relevance),
                    }
                    for result, relevance in zip(
                        results[:top_k], metrics["relevances"], strict=False
                    )
                ],
            }
        )

    strategies: dict[str, int] = {}
    for item in evaluations:
        strategy = str(item.get("strategy") or "unknown")
        strategies[strategy] = strategies.get(strategy, 0) + 1

    report = summarize_metrics(evaluations)
    report.update(
        {
            "strategies": strategies,
            "fallback_runs": sum(
                1 for item in evaluations if item.get("strategy") == "lexical_fallback"
            ),
            "evaluations": evaluations,
        }
    )

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
