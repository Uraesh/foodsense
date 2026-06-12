"""Evaluate the keyword-based lexical search strategy on the benchmark."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.search import SearchRequest 
from app.services.search_service import _lexical_search 
from eval_utils import (
    load_benchmark,
    load_catalog_texts,
    score_results,
    summarize_metrics,
)


def main() -> None:
    """Evaluate the keyword-based lexical search strategy on the benchmark."""
    report_path = Path(__file__).with_name("keyword_eval_report.json")
    benchmark = load_benchmark()
    catalog_texts = load_catalog_texts()
    evaluations: list[dict[str, object]] = []

    for item in benchmark:
        query = str(item["query"])
        top_k = int(item.get("top_k", 5))
        results = _lexical_search(SearchRequest(query=query, top_k=top_k), top_k=top_k)
        serialized_results = [result.model_dump() for result in results]
        metrics = score_results(item, serialized_results, catalog_texts)
        evaluations.append(
            {
                "query": query,
                "top_k": top_k,
                "strategy": "keyword_lexical",
                "metrics": metrics,
                "top_results": [
                    {
                        **result,
                        "relevant": bool(relevance),
                    }
                    for result, relevance in zip(
                        serialized_results[:top_k],
                        metrics["relevances"],
                        strict=False,
                    )
                ],
            }
        )

    report = summarize_metrics(evaluations)
    report.update(
        {
            "strategies": {"keyword_lexical": len(evaluations)},
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
