from __future__ import annotations

from pathlib import Path

import polars as pl

from app.config import get_settings
from app.models.product import SummaryResponse
from app.services.cache import SummaryCache

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"
SUMMARY_CACHE = SummaryCache[SummaryResponse](ttl_seconds=get_settings().summary_cache_ttl_seconds)


def _load_product_documents() -> pl.DataFrame:
    if PRODUCT_DOCUMENTS_PATH.exists():
        return pl.read_parquet(PRODUCT_DOCUMENTS_PATH)
    return pl.DataFrame(
        schema={
            "ProductId": pl.String,
            "label_hint": pl.String,
            "summary_samples": pl.List(pl.String),
            "text_samples": pl.List(pl.String),
        }
    )


async def summarize_product(product_id: str) -> SummaryResponse:
    cached = SUMMARY_CACHE.get(product_id)
    if cached is not None:
        return SummaryResponse(**cached.model_dump(), cached=True)

    products = _load_product_documents()
    match = products.filter(pl.col("ProductId") == product_id).head(1)

    if match.is_empty():
        response = SummaryResponse(
            product_id=product_id,
            summary="No product document is available yet for this identifier.",
            pros=[],
            cons=[],
            recommendation="insufficient-data",
            cached=False,
        )
        SUMMARY_CACHE.set(product_id, response)
        return response

    row = match.to_dicts()[0]
    label = row.get("label_hint") or product_id
    summary_samples = row.get("summary_samples") or []
    text_samples = row.get("text_samples") or []

    response = SummaryResponse(
        product_id=product_id,
        summary=f"'{label}' is represented by customer reviews grouped under {product_id}.",
        pros=summary_samples[:3],
        cons=text_samples[:2],
        recommendation="review-manually",
        cached=False,
    )
    SUMMARY_CACHE.set(product_id, response)
    return response
