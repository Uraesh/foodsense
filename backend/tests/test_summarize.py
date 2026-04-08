from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summarize_endpoint_returns_valid_shape() -> None:
    response = client.post("/summarize/UNKNOWN_PRODUCT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == "UNKNOWN_PRODUCT"
    assert "summary" in payload
    assert "pros" in payload
    assert "cons" in payload
