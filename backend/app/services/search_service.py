from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter

import polars as pl
from qdrant_client import QdrantClient

from app.config import get_settings
from app.models.product import ProductResult
from app.models.search import SearchRequest, SearchResponse
from app.services.embedding_service import embed_query
from app.services.rerank_service import rerank_products

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"
logger = logging.getLogger(__name__)


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


def _lexical_search(request: SearchRequest, top_k: int) -> list[ProductResult]:
    query_terms = [term.lower() for term in request.query.split() if term.strip()]
    products = _load_product_documents()
    if products.is_empty():
        return []

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

    return results


def _qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        check_compatibility=False,
    )


def _vector_search(
    query_vector: list[float],
    top_k: int,
    min_score: float | None,
) -> list[ProductResult]:
    settings = get_settings()
    client = _qdrant_client()
    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=min_score,
    )

    results: list[ProductResult] = []
    for point in response.points:
        payload = point.payload or {}
        product_id = str(payload.get("product_id") or point.id)
        results.append(
            ProductResult(
                product_id=product_id,
                title=str(payload.get("label_hint") or product_id),
                score=float(point.score or 0.0),
                avg_rating=float(payload.get("average_score") or 0.0),
                nb_reviews=int(payload.get("review_count") or 0),
            )
        )
    return results


async def search_products(request: SearchRequest) -> SearchResponse:
    started_at = perf_counter()
    settings = get_settings()
    top_k = request.top_k or settings.search_top_k
    min_score = request.min_score if request.min_score is not None else settings.search_score_threshold
    strategy = "semantic"
    warning = None

    try:
        query_vector = await embed_query(request.query)
        results = _vector_search(query_vector=query_vector, top_k=top_k, min_score=min_score)
    except Exception as exc:
        logger.warning("Semantic search fallback triggered: %s", exc)
        results = _lexical_search(request, top_k)
        strategy = "lexical_fallback"
        warning = "Semantic search temporarily unavailable; lexical fallback used."

    reranked_results = await rerank_products(results)
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    return SearchResponse(
        results=reranked_results,
        search_time_ms=elapsed_ms,
        strategy=strategy,
        warning=warning,
    )
