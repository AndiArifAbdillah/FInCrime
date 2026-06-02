"""API smoke tests (no model loading)."""
from fastapi.testclient import TestClient


def test_root_and_health():
    from src.api.main import app
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").status_code == 200
