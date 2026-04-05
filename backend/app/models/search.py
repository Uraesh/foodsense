from pydantic import BaseModel, Field

from app.models.product import ProductResult


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=10)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)


class SearchResponse(BaseModel):
    results: list[ProductResult]
    search_time_ms: int
    strategy: str = "semantic"
    warning: str | None = None
