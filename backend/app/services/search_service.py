from __future__ import annotations

from pathlib import Path
from time import perf_counter

import polars as pl

from app.config import get_settings
from app.models.product import ProductResult
from app.models.search import SearchRequest, SearchResponse
from app.services.rerank_service import rerank_products

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"


def _load_product_documents() -> pl.DataFrame:
    if PRODUCT_DOCUMENTS_PATH.exists():
        return pl.read_parquet(PRODUCT_DOCUMENTS_PATH)
    return pl.DataFrame(
        schema={
            "ProductId": pl.String,
            "label_hint": pl.String,
            "review_count": pl.Int64,
            "average_score": pl.Float64,
            "search_text": pl.String,
        }
    )


async def search_products(request: SearchRequest) -> SearchResponse:
    started_at = perf_counter()
    top_k = request.top_k or get_settings().search_top_k
    query_terms = [term.lower() for term in request.query.split() if term.strip()]

    products = _load_product_documents()
    if products.is_empty():
        return SearchResponse(results=[], search_time_ms=0)

    ranking_frame = products.with_columns(
        [
            pl.col("search_text")
            .fill_null("")
            .str.to_lowercase()
            .alias("search_text_lower")
        ]
    )

    if query_terms:
        score_expr = pl.lit(0.0)
        for term in query_terms:
            score_expr = score_expr + (
                pl.col("search_text_lower").str.count_matches(term).cast(pl.Float64)
            )
        ranking_frame = ranking_frame.with_columns(score_expr.alias("score"))
        ranking_frame = ranking_frame.filter(pl.col("score") > 0)
    else:
        ranking_frame = ranking_frame.with_columns(pl.lit(0.0).alias("score"))

    ranking_frame = ranking_frame.sort(
        ["score", "review_count", "average_score"],
        descending=[True, True, True],
    ).head(top_k)

    results = [
        ProductResult(
            product_id=row["ProductId"],
            title=row.get("label_hint") or row["ProductId"],
            score=float(row["score"]),
            avg_rating=float(row.get("average_score") or 0.0),
            nb_reviews=int(row.get("review_count") or 0),
        )
        for row in ranking_frame.to_dicts()
    ]

    reranked_results = await rerank_products(results)
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    return SearchResponse(results=reranked_results, search_time_ms=elapsed_ms)
