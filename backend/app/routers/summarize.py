from fastapi import APIRouter

from app.models.product import SummaryResponse
from app.services.summarize_service import summarize_product

router = APIRouter(tags=["summarize"])


@router.post("/summarize/{product_id}", response_model=SummaryResponse)
async def summarize(product_id: str) -> SummaryResponse:
    return await summarize_product(product_id)
