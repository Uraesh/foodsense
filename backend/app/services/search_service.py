from __future__ import annotations

import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from time import perf_counter

import polars as pl
from qdrant_client import QdrantClient

from app.config import get_settings
from app.models.product import ProductResult
from app.models.search import SearchRequest, SearchResponse
from app.services.embedding_service import embed_query
from app.services.rerank_service import rerank_products

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_DOCUMENTS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "product_documents.parquet"
)
logger = logging.getLogger(__name__)
DEFAULT_DESCRIPTION = "Produit reconstruit a partir d'avis clients agreges."
DEFAULT_CATEGORY = "Produits"


@lru_cache
def _load_product_documents() -> pl.DataFrame:
    if PRODUCT_DOCUMENTS_PATH.exists():
        products = pl.read_parquet(PRODUCT_DOCUMENTS_PATH)
    else:
        products = pl.DataFrame(
            schema={
                "ProductId": pl.String,
                "label_hint": pl.String,
                "review_count": pl.Int64,
                "average_score": pl.Float64,
                "search_text": pl.String,
            }
        )

    return products.with_columns(
        [
            pl.col("search_text")
            .fill_null("")
            .str.to_lowercase()
            .alias("search_text_lower"),
            pl.col("label_hint")
            .fill_null("")
            .str.to_lowercase()
            .alias("label_hint_lower"),
        ]
    )


def _empty_lexical_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "ProductId": pl.String,
            "label_hint": pl.String,
            "review_count": pl.Int64,
            "average_score": pl.Float64,
            "search_text_lower": pl.String,
            "label_hint_lower": pl.String,
            "lexical_score": pl.Float64,
        }
    )


def _coerce_text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _deduplicate_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", value).strip().casefold()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(value.strip())
    return deduplicated


def _clip_text(value: str, limit: int = 180) -> str:
    normalized = re.sub(r"\s+", " ", value).strip(" .|")
    if len(normalized) <= limit:
        return normalized
    shortened = normalized[:limit].rsplit(" ", 1)[0].strip(" ,;:-")
    return f"{shortened}..."


def _derive_description(metadata: dict[str, object] | None, title: str) -> str:
    if metadata is None:
        return DEFAULT_DESCRIPTION

    text_samples = _coerce_text_list(metadata.get("text_samples"))
    summary_samples = _coerce_text_list(metadata.get("summary_samples"))
    candidates = [*text_samples, *summary_samples]

    title_normalized = title.casefold().strip()
    for candidate in candidates:
        clipped = _clip_text(candidate)
        if clipped and clipped.casefold() != title_normalized:
            return clipped

    label_hint = str(metadata.get("label_hint") or "").strip()
    if label_hint:
        return f"{label_hint}."
    return DEFAULT_DESCRIPTION


def _derive_snippets(
    metadata: dict[str, object] | None,
    title: str,
    description: str,
    limit: int = 2,
) -> list[str]:
    if metadata is None:
        return []

    candidates = _deduplicate_texts(
        [
            *_coerce_text_list(metadata.get("summary_samples")),
            *_coerce_text_list(metadata.get("text_samples")),
        ]
    )
    title_normalized = title.casefold().strip()
    description_normalized = description.casefold().strip(" .")

    snippets: list[str] = []
    for candidate in candidates:
        clipped = _clip_text(candidate, limit=140)
        normalized = clipped.casefold().strip(" .")
        if not normalized:
            continue
        if normalized == title_normalized or normalized == description_normalized:
            continue
        snippets.append(clipped)
        if len(snippets) >= limit:
            break
    return snippets


def _derive_category(metadata: dict[str, object] | None, title: str) -> str:
    haystack_parts = [title]
    if metadata is not None:
        haystack_parts.extend(_coerce_text_list(metadata.get("summary_samples")))
        haystack_parts.extend(_coerce_text_list(metadata.get("text_samples")))
        haystack_parts.append(str(metadata.get("label_hint") or ""))

    haystack = " ".join(part for part in haystack_parts if part).casefold()
    category_rules = [
        ("Farines", ["flour", "farine", "meal", "baking mix", "mix"]),
        ("Chocolats", ["chocolate", "chocolat", "cocoa", "cacao"]),
        ("Cafe", ["coffee", "cafe", "espresso", "latte"]),
        ("The et infusions", ["tea", "the", "chai", "herbal", "infusion"]),
        (
            "Biscuits et snacks",
            ["cookie", "cracker", "snack", "bar", "pretzel", "chip", "biscuit"],
        ),
        ("Croquettes", ["dog", "cat", "pet food", "treat", "puppy", "kitten"]),
        ("Boissons", ["drink", "juice", "beverage", "smoothie", "soda"]),
        ("Gateaux et desserts", ["cake", "brownie", "dessert", "pudding", "muffin"]),
        ("Epices et sauces", ["spice", "seasoning", "sauce", "marinade", "dressing"]),
        ("Cereales et grains", ["cereal", "oat", "granola", "grain", "rice"]),
    ]
    for label, keywords in category_rules:
        if any(keyword in haystack for keyword in keywords):
            return label
    return DEFAULT_CATEGORY


def _angle_metrics_from_similarity(
    semantic_similarity: float | None,
) -> tuple[float | None, float | None, int | None]:
    if semantic_similarity is None:
        return None, None, None

    bounded = max(-1.0, min(1.0, float(semantic_similarity)))
    angle_radians = math.acos(bounded)
    angle_degrees = math.degrees(angle_radians)
    normalized = 1.0 - (angle_radians / (math.pi / 2))
    relevance_percent = max(0, min(100, round(normalized * 100)))
    return bounded, round(angle_degrees, 2), relevance_percent


def _fallback_relevance_percent(
    score: float, reference_score: float | None = None
) -> int:
    reference = reference_score if reference_score and reference_score > 0 else score
    if reference <= 0:
        return 0
    normalized = max(0.0, min(1.0, float(score) / float(reference)))
    return max(8, min(99, round(normalized * 100)))


def _build_product_result(
    product_id: str,
    title: str,
    score: float,
    avg_rating: float,
    nb_reviews: int,
    metadata: dict[str, object] | None = None,
    semantic_similarity: float | None = None,
    relevance_percent_override: int | None = None,
) -> ProductResult:
    bounded_similarity, angle_degrees, relevance_percent = (
        _angle_metrics_from_similarity(semantic_similarity)
    )
    if relevance_percent is None:
        relevance_percent = relevance_percent_override
    description = _derive_description(metadata, title)
    return ProductResult(
        product_id=product_id,
        title=title,
        score=float(score),
        avg_rating=float(avg_rating),
        nb_reviews=int(nb_reviews),
        description=description,
        snippets=_derive_snippets(metadata, title, description),
        category=_derive_category(metadata, title),
        semantic_similarity=bounded_similarity,
        vector_angle_degrees=angle_degrees,
        relevance_percent=relevance_percent,
    )


def _model_suffix(model_name: str) -> str:
    return model_name.replace(":", "_").replace("-", "_").replace(".", "_")


def _resolve_local_embeddings_path() -> Path:
    settings = get_settings()
    processed_dir = PROJECT_ROOT / "data" / "processed"
    candidates = [
        processed_dir
        / f"product_embeddings_{_model_suffix(settings.embedding_model)}.parquet",
        processed_dir / "product_embeddings_bge_m3.parquet",
        processed_dir / "product_embeddings.parquet",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


@lru_cache
def _load_local_embeddings() -> list[dict[str, object]]:
    embeddings_path = _resolve_local_embeddings_path()
    if not embeddings_path.exists():
        return []

    frame = pl.read_parquet(embeddings_path).select(
        [
            "ProductId",
            "label_hint",
            "review_count",
            "average_score",
            "summary_samples",
            "text_samples",
            "embedding",
        ]
    )
    rows: list[dict[str, object]] = []
    for row in frame.to_dicts():
        vector = [float(value) for value in row.get("embedding") or []]
        vector_norm = (
            math.sqrt(sum(value * value for value in vector)) if vector else 0.0
        )
        rows.append(
            {
                "ProductId": row["ProductId"],
                "label_hint": row.get("label_hint"),
                "review_count": int(row.get("review_count") or 0),
                "average_score": float(row.get("average_score") or 0.0),
                "summary_samples": row.get("summary_samples"),
                "text_samples": row.get("text_samples"),
                "embedding": vector,
                "vector_norm": vector_norm,
            }
        )
    return rows


@lru_cache
def _local_embedding_map() -> dict[str, dict[str, object]]:
    return {str(row["ProductId"]): row for row in _load_local_embeddings()}


@lru_cache
def _indexed_product_ids() -> set[str]:
    return set(_local_embedding_map().keys())


def _load_search_products() -> pl.DataFrame:
    products = _load_product_documents()
    indexed_ids = _indexed_product_ids()
    if indexed_ids:
        return products.filter(pl.col("ProductId").is_in(list(indexed_ids)))
    return products


def _cosine_similarity_from_row(
    query_vector: list[float], row: dict[str, object]
) -> float | None:
    vector = row.get("embedding") or []
    vector_norm = float(row.get("vector_norm") or 0.0)
    if not vector or vector_norm == 0.0:
        return None
    query_norm = math.sqrt(sum(value * value for value in query_vector))
    if query_norm == 0.0:
        return None
    dot_product = sum(a * b for a, b in zip(query_vector, vector, strict=False))
    return float(dot_product / (query_norm * vector_norm))


def _build_lexical_ranking(
    query: str, products: pl.DataFrame | None = None
) -> pl.DataFrame:
    query_text = query.strip().lower()
    if not query_text:
        return _empty_lexical_frame()

    products = products if products is not None else _load_search_products()
    if products.is_empty():
        return _empty_lexical_frame()

    query_terms = [term for term in query_text.split() if term.strip()]
    score_expr = (
        pl.col("search_text_lower").str.count_matches(query_text).cast(pl.Float64) * 3.0
        + pl.col("label_hint_lower").str.count_matches(query_text).cast(pl.Float64)
        * 5.0
    )
    for term in query_terms:
        score_expr = score_expr + (
            pl.col("search_text_lower").str.count_matches(term).cast(pl.Float64)
            + pl.col("label_hint_lower").str.count_matches(term).cast(pl.Float64) * 2.0
        )

    return (
        products.with_columns(score_expr.alias("lexical_score"))
        .filter(pl.col("lexical_score") > 0)
        .sort(
            ["lexical_score", "review_count", "average_score"],
            descending=[True, True, True],
        )
    )


def _score_to_map(frame: pl.DataFrame, score_column: str) -> dict[str, float]:
    return {
        row["ProductId"]: float(row[score_column])
        for row in frame.select(["ProductId", score_column]).to_dicts()
    }


def _metadata_by_product(
    products: pl.DataFrame, product_ids: list[str]
) -> dict[str, dict[str, object]]:
    if not product_ids:
        return {}
    return {
        row["ProductId"]: row
        for row in products.filter(pl.col("ProductId").is_in(product_ids)).to_dicts()
    }


def _indexed_product_count() -> int:
    indexed_ids = _indexed_product_ids()
    if indexed_ids:
        return len(indexed_ids)
    products = _load_search_products()
    return products.height


def _lexical_search(request: SearchRequest, top_k: int) -> list[ProductResult]:
    products = _load_search_products()
    ranking_frame = _build_lexical_ranking(request.query, products).head(top_k)
    rows = ranking_frame.to_dicts()
    max_score = max((float(row["lexical_score"]) for row in rows), default=0.0)
    return [
        _build_product_result(
            product_id=row["ProductId"],
            title=row.get("label_hint") or row["ProductId"],
            score=float(row["lexical_score"]),
            avg_rating=float(row.get("average_score") or 0.0),
            nb_reviews=int(row.get("review_count") or 0),
            metadata=row,
            semantic_similarity=None,
            relevance_percent_override=_fallback_relevance_percent(
                float(row["lexical_score"]),
                max_score,
            ),
        )
        for row in rows
    ]


def _qdrant_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url_override:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=settings.qdrant_timeout_seconds,
            check_compatibility=False,
        )
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key or None,
        timeout=settings.qdrant_timeout_seconds,
        check_compatibility=False,
    )


def _local_vector_search(
    query_vector: list[float],
    top_k: int,
    min_score: float | None,
) -> list[ProductResult]:
    if not query_vector:
        return []

    query_norm = math.sqrt(sum(value * value for value in query_vector))
    if query_norm == 0.0:
        return []

    scored_results: list[ProductResult] = []
    for row in _load_local_embeddings():
        vector = row["embedding"]
        vector_norm = float(row["vector_norm"])
        if not vector or vector_norm == 0.0:
            continue
        dot_product = sum(a * b for a, b in zip(query_vector, vector, strict=False))
        score = dot_product / (query_norm * vector_norm)
        if min_score is not None and score < min_score:
            continue
        scored_results.append(
            _build_product_result(
                product_id=str(row["ProductId"]),
                title=str(row.get("label_hint") or row["ProductId"]),
                score=float(score),
                avg_rating=float(row.get("average_score") or 0.0),
                nb_reviews=int(row.get("review_count") or 0),
                metadata=row,
                semantic_similarity=float(score),
            )
        )

    scored_results.sort(
        key=lambda item: (item.score, item.nb_reviews, item.avg_rating),
        reverse=True,
    )
    return scored_results[:top_k]


def _vector_search(
    query_vector: list[float],
    top_k: int,
    min_score: float | None,
) -> list[ProductResult]:
    settings = get_settings()
    try:
        client = _qdrant_client()
        response = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            score_threshold=min_score,
        )

        results: list[ProductResult] = []
        for point in response.points:
            payload = point.payload or {}
            product_id = str(payload.get("product_id") or point.id)
            results.append(
                _build_product_result(
                    product_id=product_id,
                    title=str(payload.get("label_hint") or product_id),
                    score=float(point.score or 0.0),
                    avg_rating=float(payload.get("average_score") or 0.0),
                    nb_reviews=int(payload.get("review_count") or 0),
                    metadata=payload,
                    semantic_similarity=float(point.score or 0.0),
                )
            )
        return results
    except Exception as exc:
        logger.warning("Qdrant unavailable, using local semantic index: %s", exc)
        return _local_vector_search(
            query_vector=query_vector,
            top_k=top_k,
            min_score=min_score,
        )


def _hybrid_search(
    request: SearchRequest,
    query_vector: list[float],
    top_k: int,
    min_score: float | None,
) -> list[ProductResult]:
    settings = get_settings()
    products = _load_search_products()
    candidate_pool = max(top_k, settings.search_candidate_pool)

    lexical_frame = _build_lexical_ranking(request.query, products).head(candidate_pool)
    semantic_results = _vector_search(
        query_vector=query_vector,
        top_k=candidate_pool,
        min_score=min_score,
    )

    lexical_scores = _score_to_map(lexical_frame, "lexical_score")
    semantic_scores = {
        result.product_id: (
            result.semantic_similarity
            if result.semantic_similarity is not None
            else result.score
        )
        for result in semantic_results
    }
    candidate_ids = list(
        dict.fromkeys([*semantic_scores.keys(), *lexical_scores.keys()])
    )
    metadata_map = _metadata_by_product(products, candidate_ids)
    embedding_map = _local_embedding_map()

    for product_id in candidate_ids:
        if product_id in semantic_scores:
            continue
        row = embedding_map.get(product_id)
        if row is None:
            continue
        similarity = _cosine_similarity_from_row(query_vector, row)
        if similarity is not None:
            semantic_scores[product_id] = similarity

    semantic_max = max(semantic_scores.values(), default=0.0)
    lexical_max = max(lexical_scores.values(), default=0.0)
    query_text = request.query.strip().lower()

    ranked_results: list[ProductResult] = []
    for product_id in candidate_ids:
        metadata = metadata_map.get(product_id, {})
        title = str(metadata.get("label_hint") or product_id)
        review_count = int(metadata.get("review_count") or 0)
        average_score = float(metadata.get("average_score") or 0.0)
        search_text_lower = str(metadata.get("search_text_lower") or "")
        title_lower = str(metadata.get("label_hint_lower") or title.lower())

        semantic_score = semantic_scores.get(product_id, 0.0)
        lexical_score = lexical_scores.get(product_id, 0.0)
        semantic_norm = semantic_score / semantic_max if semantic_max else 0.0
        lexical_norm = lexical_score / lexical_max if lexical_max else 0.0
        exact_phrase_bonus = (
            0.08
            if query_text
            and (query_text in title_lower or query_text in search_text_lower)
            else 0.0
        )
        rating_boost = min(average_score / 5.0, 1.0) * 0.02
        review_boost = min(math.log1p(review_count) / 5.0, 1.0) * 0.03

        combined_score = (
            settings.search_semantic_weight * semantic_norm
            + settings.search_lexical_weight * lexical_norm
            + exact_phrase_bonus
            + rating_boost
            + review_boost
        )

        ranked_results.append(
            _build_product_result(
                product_id=product_id,
                title=title,
                score=round(combined_score, 6),
                avg_rating=average_score,
                nb_reviews=review_count,
                metadata=metadata,
                semantic_similarity=semantic_scores.get(product_id),
            )
        )

    ranked_results.sort(
        key=lambda item: (item.score, item.nb_reviews, item.avg_rating),
        reverse=True,
    )
    top_results = ranked_results[:top_k]
    max_score = max((result.score for result in top_results), default=0.0)
    adjusted_results: list[ProductResult] = []
    for result in top_results:
        if result.relevance_percent is None:
            result = result.model_copy(
                update={
                    "relevance_percent": _fallback_relevance_percent(
                        result.score, max_score
                    )
                }
            )
        adjusted_results.append(result)
    return adjusted_results


async def search_products(request: SearchRequest) -> SearchResponse:
    started_at = perf_counter()
    settings = get_settings()
    top_k = request.top_k or settings.search_top_k
    min_score = (
        request.min_score
        if request.min_score is not None
        else settings.search_score_threshold
    )
    strategy = "semantic_hybrid"
    warning = None
    total_indexed = _indexed_product_count()

    if request.mode == "keyword":
        results = _lexical_search(request, top_k)
        strategy = "keyword_only"
    else:
        try:
            query_vector = await embed_query(request.query)
            results = _hybrid_search(
                request=request,
                query_vector=query_vector,
                top_k=top_k,
                min_score=min_score,
            )
        except Exception as exc:
            logger.warning("Semantic search fallback triggered: %s", exc)
            results = _lexical_search(request, top_k)
            strategy = "lexical_fallback"
            warning = "Semantic search temporarily unavailable; lexical fallback used."

    reranked_results = await rerank_products(results)
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    return SearchResponse(
        results=reranked_results,
        search_time_ms=elapsed_ms,
        strategy=strategy,
        warning=warning,
        total_indexed=total_indexed,
    )
