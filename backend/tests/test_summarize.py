"""Unit tests for the summarize endpoint of the FoodSense backend application."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summarize_endpoint_returns_valid_shape() -> None:
    """Test that the /summarize/{product_id} endpoint returns a 200 status code and a JSON response with the expected structure, including product_id, product_label, summary, pros, cons, and source_basis fields."""
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
    """Test that the /summarize/{product_id} endpoint returns a 200 status code and a JSON response with the expected structure, including product_id and summary fields."""
    response = client.get("/summarize/UNKNOWN_PRODUCT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == "UNKNOWN_PRODUCT"
    assert "summary" in payload


def test_summarize_help_endpoint_returns_usage_message() -> None:
    """Test that the /summarize endpoint returns a 200 status code and a JSON response containing a message that provides usage instructions for the endpoint."""
    response = client.get("/summarize")

    assert response.status_code == 200
    assert "Use /summarize/{product_id}" in response.json()["message"]
