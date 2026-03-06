"""Tests for FastAPI routes (unit tests, no Redis needed)."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-research-ppt-backend"


class TestSessionEndpoints:
    def test_get_nonexistent_session(self, client):
        response = client.get("/api/v1/sessions/nonexistent-id/status")
        assert response.status_code == 404

    def test_resume_nonexistent_session(self, client):
        response = client.post(
            "/api/v1/sessions/nonexistent-id/resume",
            json={"action": "approve"},
        )
        assert response.status_code == 404

    def test_download_nonexistent_ppt(self, client):
        response = client.get("/api/v1/sessions/nonexistent-id/ppt/download")
        assert response.status_code == 404

    def test_download_nonexistent_doc(self, client):
        response = client.get("/api/v1/sessions/nonexistent-id/doc/download")
        assert response.status_code == 404
