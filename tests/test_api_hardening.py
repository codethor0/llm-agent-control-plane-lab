"""API boundary hardening tests for production deployment profile."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from agent_control_plane.api import create_app
from agent_control_plane.config import AppConfig, EnvironmentMode

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "policies" / "default.yaml"
FAKE_API_KEY = "lab-fake-api-key-test-only"


def _run_payload() -> dict[str, object]:
    return {
        "request_id": "api-hardening-1",
        "user_id": "user-1",
        "session_id": "sess-1",
        "tenant_id": "tenant-a",
        "role": "user",
        "user_message": "read",
        "scenario": "safe_read",
        "path": "protected",
    }


def _production_app(tmp_path: Path) -> TestClient:
    cfg = AppConfig(
        environment_mode=EnvironmentMode.PRODUCTION,
        require_api_auth=True,
        allowed_api_keys_file=None,
        allowed_origins=("https://app.example.invalid",),
        max_request_body_bytes=4_096,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=False,
        provenance_hmac_key_file=None,
        require_approval_token=False,
        enable_rate_limit_guidance=True,
        enable_debug_errors=False,
        allow_live_external_tools=False,
        allow_shell_tools=False,
        policy_path=POLICY_PATH,
        _api_keys=frozenset({FAKE_API_KEY}),
    )
    return TestClient(create_app(cfg))


def _local_app(tmp_path: Path) -> TestClient:
    cfg = AppConfig(
        environment_mode=EnvironmentMode.LOCAL,
        require_api_auth=False,
        allowed_api_keys_file=None,
        allowed_origins=("http://127.0.0.1:8080",),
        max_request_body_bytes=1_048_576,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=False,
        provenance_hmac_key_file=None,
        require_approval_token=False,
        enable_rate_limit_guidance=True,
        enable_debug_errors=True,
        allow_live_external_tools=False,
        allow_shell_tools=False,
        policy_path=POLICY_PATH,
        _api_keys=frozenset(),
    )
    return TestClient(create_app(cfg))


def test_health_works_without_auth(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_requires_auth(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post("/run", json=_run_payload())
    assert response.status_code == 401
    assert response.json()["detail"] == "unauthorized"


def test_missing_api_key_denied(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post("/run", json=_run_payload(), headers={})
    assert response.status_code == 401


def test_wrong_api_key_denied(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post(
        "/run",
        json=_run_payload(),
        headers={"X-API-Key": "lab-fake-wrong-key"},
    )
    assert response.status_code == 401


def test_correct_fake_api_key_accepted(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post(
        "/run",
        json=_run_payload(),
        headers={"X-API-Key": FAKE_API_KEY},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True


def test_bearer_api_key_accepted(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post(
        "/run",
        json=_run_payload(),
        headers={"Authorization": f"Bearer {FAKE_API_KEY}"},
    )
    assert response.status_code == 200


def test_large_request_body_denied(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    oversized = 5_000
    response = client.post(
        "/run",
        json=_run_payload(),
        headers={
            "X-API-Key": FAKE_API_KEY,
            "Content-Length": str(oversized),
            "Content-Type": "application/json",
        },
        content=b"{}",
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "request_entity_too_large"


def test_production_validation_error_hides_details(tmp_path: Path) -> None:
    client = _production_app(tmp_path)
    response = client.post(
        "/run",
        json={"request_id": "only-field"},
        headers={"X-API-Key": FAKE_API_KEY},
    )
    assert response.status_code == 422
    body = response.text.lower()
    assert "traceback" not in body
    assert response.json()["detail"] == "validation_error"


def test_local_mode_run_without_auth(tmp_path: Path) -> None:
    client = _local_app(tmp_path)
    response = client.post("/run", json=_run_payload())
    assert response.status_code == 200
    assert response.json()["allowed"] is True
