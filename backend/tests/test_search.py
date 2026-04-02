from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_endpoint_returns_valid_shape() -> None:
    response = client.post("/search", json={"query": "dark chocolate", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert "search_time_ms" in payload
