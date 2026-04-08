from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Sequence

import httpx

from app.config import get_settings
from app.services.cache import SummaryCache


@lru_cache
def _embedding_cache() -> SummaryCache[list[float]]:
    settings = get_settings()
    return SummaryCache(ttl_seconds=settings.embedding_cache_ttl_seconds)


async def embed_query(text: str) -> list[float]:
    settings = get_settings()
    safe_text = text.strip()
    if not safe_text:
        raise ValueError("Query text cannot be empty.")
    if settings.embedding_query_max_chars > 0:
        safe_text = safe_text[: settings.embedding_query_max_chars]
    cache_key = safe_text.casefold()
    cached_embedding = _embedding_cache().get(cache_key)
    if cached_embedding is not None:
        return cached_embedding

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
        for attempt in range(4):
            try:
                response = await client.post(
                    f"{settings.ollama_host}/api/embeddings",
                    json={
                        "model": settings.embedding_model,
                        "prompt": safe_text,
                        "keep_alive": settings.ollama_keep_alive,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                embedding = payload["embedding"]
                _embedding_cache().set(cache_key, embedding)
                return embedding
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < 3:
                    await asyncio.sleep(2.0 + attempt)

    raise RuntimeError(
        f"Failed to generate query embedding with model '{settings.embedding_model}'."
    ) from last_error


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for text in texts:
        embeddings.append(await embed_query(text))
    return embeddings


async def warmup_embedding_model() -> None:
    try:
        await embed_query("semantic search warmup")
    except Exception:
        # Warmup is a best-effort optimization for local demos and evaluation.
        return
