from fastapi import APIRouter, Query

from app.models.search import SearchRequest, SearchResponse
from app.services.search_service import search_products

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    return await search_products(request)


@router.get("/search", response_model=SearchResponse)
async def search_get(
    query: str = Query(..., min_length=1),
    top_k: int | None = Query(default=None, ge=1, le=10),
    min_score: float | None = Query(default=None, ge=-1.0, le=1.0),
    mode: str = Query(default="semantic", pattern="^(semantic|keyword)$"),
) -> SearchResponse:
    return await search_products(
        SearchRequest(query=query, top_k=top_k, min_score=min_score, mode=mode)
    )
