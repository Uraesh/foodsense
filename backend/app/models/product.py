from pydantic import BaseModel, Field


class ProductResult(BaseModel):
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="User-facing product title or inferred label")
    score: float = Field(..., description="Search relevance score")
    avg_rating: float = Field(..., description="Average review rating")
    nb_reviews: int = Field(..., description="Number of reviews aggregated for the product")


class SummaryResponse(BaseModel):
    product_id: str
    summary: str
    pros: list[str]
    cons: list[str]
    recommendation: str
    cached: bool
