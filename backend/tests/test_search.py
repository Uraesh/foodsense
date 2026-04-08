from fastapi.testclient import TestClient

from app.models.product import ProductResult
from app.main import app
from app.services import search_service

client = TestClient(app)


def test_search_endpoint_returns_valid_shape() -> None:
    response = client.post("/search", json={"query": "dark chocolate", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert "search_time_ms" in payload
    assert "strategy" in payload
    assert "warning" in payload


def test_search_get_endpoint_returns_valid_shape() -> None:
    response = client.get("/search", params={"query": "dark chocolate", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert "search_time_ms" in payload
    assert "strategy" in payload


def test_search_endpoint_can_report_semantic_strategy(monkeypatch) -> None:
    async def fake_embed_query(_: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def fake_hybrid_search(
        request,
        query_vector: list[float],
        top_k: int,
        min_score: float | None,
    ) -> list[ProductResult]:
        assert request.query == "dark chocolate"
        assert query_vector == [0.1, 0.2, 0.3]
        assert top_k == 3
        assert min_score is None
        return [
            ProductResult(
                product_id="BTEST123",
                title="Semantic hit",
                score=0.91,
                avg_rating=4.7,
                nb_reviews=42,
            )
        ]

    monkeypatch.setattr("app.services.search_service.embed_query", fake_embed_query)
    monkeypatch.setattr("app.services.search_service._hybrid_search", fake_hybrid_search)

    response = client.post("/search", json={"query": "dark chocolate", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "semantic_hybrid"
    assert payload["warning"] is None
    assert payload["results"][0]["product_id"] == "BTEST123"


def test_vector_search_uses_local_semantic_fallback(monkeypatch) -> None:
    def fake_qdrant_client():
        raise RuntimeError("qdrant down")

    def fake_local_vector_search(
        query_vector: list[float],
        top_k: int,
        min_score: float | None,
    ) -> list[ProductResult]:
        assert query_vector == [0.1, 0.2, 0.3]
        assert top_k == 2
        assert min_score == 0.4
        return [
            ProductResult(
                product_id="BLOCAL123",
                title="Local semantic hit",
                score=0.88,
                avg_rating=4.5,
                nb_reviews=10,
            )
        ]

    monkeypatch.setattr(search_service, "_qdrant_client", fake_qdrant_client)
    monkeypatch.setattr(search_service, "_local_vector_search", fake_local_vector_search)

    results = search_service._vector_search([0.1, 0.2, 0.3], top_k=2, min_score=0.4)

    assert results[0].product_id == "BLOCAL123"
