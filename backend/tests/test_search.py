from fastapi.testclient import TestClient

from app.models.product import ProductResult
from app.main import app

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

    def fake_vector_search(
        query_vector: list[float],
        top_k: int,
        min_score: float | None,
    ) -> list[ProductResult]:
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
    monkeypatch.setattr("app.services.search_service._vector_search", fake_vector_search)

    response = client.post("/search", json={"query": "dark chocolate", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy"] == "semantic"
    assert payload["warning"] is None
    assert payload["results"][0]["product_id"] == "BTEST123"
