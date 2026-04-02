from fastapi import APIRouter

from app.models.search import SearchRequest, SearchResponse
from app.services.search_service import search_products

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    return await search_products(request)
