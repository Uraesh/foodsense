from fastapi import APIRouter

from app.models.product import SummaryResponse
from app.services.summarize_service import summarize_product

router = APIRouter(tags=["summarize"])


@router.get("/summarize")
async def summarize_help() -> dict[str, str]:
    return {
        "message": "Use /summarize/{product_id} with GET or POST to retrieve a product summary."
    }


@router.post("/summarize/{product_id}", response_model=SummaryResponse)
async def summarize(product_id: str) -> SummaryResponse:
    return await summarize_product(product_id)


@router.get("/summarize/{product_id}", response_model=SummaryResponse)
async def summarize_get(product_id: str) -> SummaryResponse:
    return await summarize_product(product_id)
