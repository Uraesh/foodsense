from __future__ import annotations

import json
from pathlib import Path
import re

import httpx

import polars as pl

from app.config import get_settings
from app.models.product import SummaryResponse
from app.services.cache import SummaryCache

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"
SUMMARY_CACHE = SummaryCache[SummaryResponse](ttl_seconds=get_settings().summary_cache_ttl_seconds)


def _load_product_documents() -> pl.DataFrame:
    if PRODUCT_DOCUMENTS_PATH.exists():
        return pl.read_parquet(PRODUCT_DOCUMENTS_PATH)
    return pl.DataFrame(
        schema={
            "ProductId": pl.String,
            "label_hint": pl.String,
            "summary_samples": pl.List(pl.String),
            "text_samples": pl.List(pl.String),
        }
    )


def _normalize_list(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    text = str(values).strip()
    return [text] if text else []


def _clip_text(value: str, limit: int = 180) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" .|")
    if len(normalized) <= limit:
        return normalized
    shortened = normalized[:limit].rsplit(" ", 1)[0].strip(" ,;:-")
    return f"{shortened}..."


def _fallback_summary(product_id: str, row: dict[str, object]) -> SummaryResponse:
    label = str(row.get("label_hint") or product_id)
    summary_samples = _normalize_list(row.get("summary_samples"))
    text_samples = _normalize_list(row.get("text_samples"))
    snippets = [_clip_text(item, limit=140) for item in [*summary_samples, *text_samples] if item.strip()]
    snippets = list(dict.fromkeys(snippets))
    pros = snippets[:3]
    cons = snippets[3:5]
    review_count = int(row.get("review_count") or 0)
    average_score = float(row.get("average_score") or 0.0)

    return SummaryResponse(
        product_id=product_id,
        product_label=label,
        summary=(
            f"{label} est resume a partir de {review_count} avis agreges, avec une note moyenne "
            f"de {average_score:.1f}/5. Cette synthese reste fondee sur les avis clients de la base."
        ),
        pros=pros,
        cons=cons,
        recommendation=(
            f"Produit correspondant retenu : {label} ({product_id}). "
            "A verifier selon ton besoin reel ; aucune source nutritionnelle externe n'est encore branchee a cette V1."
        ),
        cached=False,
        source_basis="customer-reviews",
    )


def _extract_json_payload(raw_text: str) -> dict[str, object] | None:
    text = raw_text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


async def _generate_llm_summary(product_id: str, row: dict[str, object]) -> SummaryResponse | None:
    settings = get_settings()
    label = str(row.get("label_hint") or product_id)
    summary_samples = _normalize_list(row.get("summary_samples"))[:4]
    text_samples = _normalize_list(row.get("text_samples"))[:4]
    average_score = float(row.get("average_score") or 0.0)
    review_count = int(row.get("review_count") or 0)

    prompt = f"""
Tu es un assistant de synthese produit pour FoodSense.
Tu resumes uniquement les avis clients agreges. Tu n'inventes aucune source nutritionnelle externe.
Produit: {label}
ProductId: {product_id}
Note moyenne: {average_score:.2f}/5
Nombre d'avis: {review_count}
Extraits de resumes: {summary_samples}
Extraits d'avis: {text_samples}

Retourne uniquement un JSON valide de la forme:
{{
  "summary": "...",
  "pros": ["..."],
  "cons": ["..."],
  "recommendation": "..."
}}

La recommandation doit mentionner explicitement le produit correspondant `{label}` ou `{product_id}` et rappeler qu'elle est basee sur les avis clients.
""".strip()

    try:
        async with httpx.AsyncClient(timeout=25.0, trust_env=False) as client:
            response = await client.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": settings.summary_model,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "0s",
                },
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return None

    payload = _extract_json_payload(response.json().get("response", ""))
    if payload is None:
        return None

    return SummaryResponse(
        product_id=product_id,
        product_label=label,
        summary=str(payload.get("summary") or "").strip()
        or f"Synthese indisponible pour {label}.",
        pros=[str(item).strip() for item in payload.get("pros", []) if str(item).strip()][:3],
        cons=[str(item).strip() for item in payload.get("cons", []) if str(item).strip()][:3],
        recommendation=str(payload.get("recommendation") or "").strip()
        or f"Produit correspondant : {label} ({product_id}).",
        cached=False,
        source_basis="customer-reviews",
    )


async def summarize_product(product_id: str) -> SummaryResponse:
    cached = SUMMARY_CACHE.get(product_id)
    if cached is not None:
        return SummaryResponse(**cached.model_dump(), cached=True)

    settings = get_settings()
    products = _load_product_documents()
    match = products.filter(pl.col("ProductId") == product_id).head(1)

    if match.is_empty():
        response = SummaryResponse(
            product_id=product_id,
            product_label=product_id,
            summary="No product document is available yet for this identifier.",
            pros=[],
            cons=[],
            recommendation="insufficient-data",
            cached=False,
            source_basis="customer-reviews",
        )
        SUMMARY_CACHE.set(product_id, response)
        return response

    row = match.to_dicts()[0]
    response = None
    if settings.summary_strategy == "ollama":
        response = await _generate_llm_summary(product_id, row)
    if response is None:
        response = _fallback_summary(product_id, row)
    SUMMARY_CACHE.set(product_id, response)
    return response
