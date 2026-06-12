from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summarize_endpoint_returns_valid_shape() -> None:
    response = client.post("/summarize/UNKNOWN_PRODUCT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == "UNKNOWN_PRODUCT"
    assert "product_label" in payload
    assert "summary" in payload
    assert "pros" in payload
    assert "cons" in payload
    assert "source_basis" in payload


def test_summarize_get_endpoint_returns_valid_shape() -> None:
    response = client.get("/summarize/UNKNOWN_PRODUCT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == "UNKNOWN_PRODUCT"
    assert "summary" in payload


def test_summarize_help_endpoint_returns_usage_message() -> None:
    response = client.get("/summarize")

    assert response.status_code == 200
    assert "Use /summarize/{product_id}" in response.json()["message"]
