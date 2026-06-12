"""Configuration management for the FoodSense backend application."""
from functools import lru_cache
from urllib.parse import quote_plus
import re

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env files."""
    app_name: str = "FoodSense Backend"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_api_base_url: str = "http://localhost:3000"
    database_url: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "Foodsense"
    postgres_user: str = "postgres"
    postgres_password: str = "yusuke"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url_override: str = Field(default="", validation_alias="QDRANT_URL")
    qdrant_api_key: str = ""
    qdrant_collection: str = "foodsense_products_v2"
    qdrant_timeout_seconds: float = 1.5
    ollama_host: str = "http://127.0.0.1:11434"
    embedding_model: str = "bge-m3"
    ollama_keep_alive: str = "2m"
    embedding_query_max_chars: int = 512
    rerank_model: str = "qwen3:4b"
    summary_model: str = "mistral"
    # Default to using the Ollama-backed LLM (mistral) for summaries so that
    # Mistral is the out-of-the-box summarization backend. Set SUMMARY_STRATEGY
    # to 'extractive' to use the fallback extractive summarizer.
    summary_strategy: str = "ollama"
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    search_top_k: int = 10
    search_score_threshold: float | None = None
    search_candidate_pool: int = 20
    search_semantic_weight: float = 0.65
    search_lexical_weight: float = 0.35
    embedding_cache_ttl_seconds: int = 900
    summary_cache_ttl_seconds: int = 3600

    @property
    def frontend_api_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in re.split(r"\s*,\s*", self.frontend_api_base_url)
            if origin.strip()
        ]
        if not origins:
            origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        if "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        if "http://127.0.0.1:3000" not in origins:
            origins.append("http://127.0.0.1:3000")
        return origins

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password) if self.postgres_password else ""
        auth = f"{user}:{password}@" if password else f"{user}@"
        return f"postgresql://{auth}{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("search_score_threshold", mode="before")
    @classmethod
    def empty_threshold_to_none(cls, value):
        """Convert empty string or None to None for search_score_threshold, allowing it to be optional."""
        if value in ("", None):
            return None
        return value

    @field_validator("search_semantic_weight", "search_lexical_weight")
    @classmethod
    def validate_weights(cls, value: float) -> float:
        """Ensure that search weights are between 0 and 1 to maintain a valid weighting scheme for semantic and lexical search components."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("Search weights must be between 0 and 1.")
        return value

    @field_validator("summary_strategy")
    @classmethod
    def validate_summary_strategy(cls, value: str) -> str:
        """Validate that the summary strategy is either 'extractive' or 'ollama', ensuring that the application uses a supported summarization approach."""
        normalized = value.strip().lower()
        if normalized not in {"extractive", "ollama"}:
            raise ValueError(
                "SUMMARY_STRATEGY must be either 'extractive' or 'ollama'."
            )
        return normalized

    @property
    def qdrant_url(self) -> str:
        """Construct the Qdrant URL from host and port, or use the override if provided."""
        if self.qdrant_url_override:
            return self.qdrant_url_override
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
