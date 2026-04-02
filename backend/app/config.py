from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FoodSense Backend"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_api_base_url: str = "http://localhost:8000"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    ollama_host: str = "http://localhost:11434"
    embedding_model: str = "qwen3-embedding:0.6b"
    rerank_model: str = "qwen3:4b"
    summary_model: str = "mistral-small-3.1"
    mistral_api_key: str = ""
    openrouter_api_key: str = ""
    search_top_k: int = 10
    summary_cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
