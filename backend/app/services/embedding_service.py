from __future__ import annotations

import asyncio
from typing import Sequence

import httpx

from app.config import get_settings


async def embed_query(text: str) -> list[float]:
    settings = get_settings()
    safe_text = text.strip()
    if not safe_text:
        raise ValueError("Query text cannot be empty.")

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(
                    f"{settings.ollama_host}/api/embeddings",
                    json={"model": settings.embedding_model, "prompt": safe_text},
                )
                response.raise_for_status()
                payload = response.json()
                return payload["embedding"]
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(1.5)

    raise RuntimeError(
        f"Failed to generate query embedding with model '{settings.embedding_model}'."
    ) from last_error


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for text in texts:
        embeddings.append(await embed_query(text))
    return embeddings
