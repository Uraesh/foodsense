from __future__ import annotations

from typing import Sequence


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Placeholder embedding service wired for later Ollama integration."""
    return [[float(len(text))] for text in texts]
