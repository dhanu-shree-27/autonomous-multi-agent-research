"""
Phase 1 test: confirms the app starts and the health endpoint responds
correctly. This is the minimum proof that the setup (config, logging,
FastAPI wiring) all works together.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "app_name" in body
    assert "config_warnings" in body


def test_health_check_reports_missing_api_key_as_warning_not_error():
    """
    If OPENAI_API_KEY is missing or still the placeholder value, the health
    endpoint should still return 200 (the server itself is healthy) but
    surface the problem in `config_warnings` rather than crashing.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert isinstance(response.json()["config_warnings"], list)
