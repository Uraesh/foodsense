from pydantic import BaseModel, Field


class ProductResult(BaseModel):
    product_id: str = Field(..., description="Unique product identifier")
    title: str = Field(..., description="User-facing product title or inferred label")
    score: float = Field(..., description="Search relevance score")
    avg_rating: float = Field(..., description="Average review rating")
    nb_reviews: int = Field(..., description="Number of reviews aggregated for the product")
    description: str = Field(
        default="",
        description="Short customer-facing description inferred from review snippets",
    )
    category: str = Field(
        default="Produits",
        description="Inferred family/category label used for display",
    )
    semantic_similarity: float | None = Field(
        default=None,
        description="Raw cosine similarity between query and product embedding when available",
    )
    vector_angle_degrees: float | None = Field(
        default=None,
        description="Angle in degrees derived from cosine similarity",
    )
    relevance_percent: int | None = Field(
        default=None,
        description="Display percentage derived from the vector angle",
    )


class SummaryResponse(BaseModel):
    product_id: str
    summary: str
    pros: list[str]
    cons: list[str]
    recommendation: str
    cached: bool
