from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon_endpoint_returns_no_content() -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 204
