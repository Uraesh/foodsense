from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FoodSense Backend"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_api_base_url: str = "http://localhost:8000"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "foodsense_products_bge_m3"
    qdrant_timeout_seconds: float = 1.5
    ollama_host: str = "http://127.0.0.1:11434"
    embedding_model: str = "bge-m3"
    ollama_keep_alive: str = "2m"
    embedding_query_max_chars: int = 512
    rerank_model: str = "qwen3:4b"
    summary_model: str = "mistral-small-3.1"
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    search_top_k: int = 10
    search_score_threshold: float | None = None
    search_candidate_pool: int = 20
    search_semantic_weight: float = 0.65
    search_lexical_weight: float = 0.35
    embedding_cache_ttl_seconds: int = 900
    summary_cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("search_score_threshold", mode="before")
    @classmethod
    def empty_threshold_to_none(cls, value):
        if value in ("", None):
            return None
        return value

    @field_validator("search_semantic_weight", "search_lexical_weight")
    @classmethod
    def validate_weights(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Search weights must be between 0 and 1.")
        return value

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
