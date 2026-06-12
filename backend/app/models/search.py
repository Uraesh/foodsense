"""Data models for search requests and responses."""
from pydantic import BaseModel, Field

from app.models.product import ProductResult


class SearchRequest(BaseModel):
    """Represents a search request with query parameters."""
    query: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=10)
    min_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    mode: str = Field(default="semantic", pattern="^(semantic|keyword)$")


class SearchResponse(BaseModel):
    """Represents a search response containing results and metadata."""
    results: list[ProductResult]
    search_time_ms: int
    strategy: str = "semantic"
    warning: str | None = None
    total_indexed: int = 0
