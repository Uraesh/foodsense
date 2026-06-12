""""Unit tests for the health check and favicon endpoints of the FoodSense backend application."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    """Test that the /health endpoint returns a 200 status code and the expected JSON response indicating that the backend is healthy."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon_endpoint_returns_no_content() -> None:
    """Test that the /favicon.ico endpoint returns a 204 No Content status code, indicating that there is no favicon provided."""
    response = client.get("/favicon.ico")

    assert response.status_code == 204
