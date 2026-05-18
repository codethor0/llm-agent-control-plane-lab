"""FastAPI demo API tests."""

from fastapi.testclient import TestClient

from agent_control_plane.api import get_app


def test_health_endpoint() -> None:
    client = TestClient(get_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_protected_safe_read() -> None:
    client = TestClient(get_app())
    response = client.post(
        "/run",
        json={
            "request_id": "api-1",
            "user_id": "user-1",
            "session_id": "sess-1",
            "tenant_id": "tenant-a",
            "role": "user",
            "user_message": "read",
            "scenario": "safe_read",
            "path": "protected",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True
