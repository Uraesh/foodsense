from __future__ import annotations

from app.models.product import ProductResult


async def rerank_products(products: list[ProductResult]) -> list[ProductResult]:
    """Placeholder reranking pass kept for architectural completeness."""
    return products
