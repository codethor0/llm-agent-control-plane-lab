"""Observability and audit correlation tests (P9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.llm_adapter import (
    LLMAdapterError,
    LLMAdapterMode,
    create_llm_adapter,
)
from agent_control_plane.models import AgentRequest
from agent_control_plane.observability import normalize_correlation_id, resolve_correlation_id
from agent_control_plane.pipeline import ControlPlanePipeline

FAKE_API_KEY = "lab-fake-api-key-test-only"
FAKE_SECRET = "sk-live-FAKE-TEST-ONLY-audit-observability-check"


@pytest.fixture
def correlation_request(base_request: AgentRequest) -> AgentRequest:
    return base_request.model_copy(
        update={
            "request_id": "req-corr-1",
            "correlation_id": "corr-session-abc",
        }
    )


def test_every_audit_event_has_request_id(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "safe_read"}))
    for event in audit_logger.read_events():
        assert event.get("request_id")


def test_every_audit_event_has_event_type(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    for event in audit_logger.read_events():
        assert event.get("event_type")


def test_blocked_decisions_include_safe_reason(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    blocked = [e for e in audit_logger.read_events() if e["allowed"] is False]
    assert blocked
    for event in blocked:
        assert isinstance(event["policy_reason"], str)
        assert event["policy_reason"]
        assert FAKE_SECRET not in event["policy_reason"]


def test_output_filter_events_use_redacted_findings_only(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    events = [e for e in audit_logger.read_events() if e["event_type"] == "output_filter_blocked"]
    assert events
    for event in events:
        redacted = event.get("output_findings_redacted") or []
        for finding in redacted:
            assert "redacted_sample" in finding
            assert "rule_id" in finding
            raw = str(finding)
            assert "sk-live-FAKE" not in raw


def test_api_auth_failure_does_not_log_api_key(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from agent_control_plane.api import create_app
    from agent_control_plane.config import AppConfig, EnvironmentMode
    from agent_control_plane.llm_adapter import LLMAdapterMode

    policy_path = Path(__file__).resolve().parents[1] / "policies" / "default.yaml"
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
        llm_adapter_mode=LLMAdapterMode.SIMULATED,
        allow_live_llm_calls=False,
        llm_provider_name=None,
        llm_model_name=None,
        policy_path=policy_path,
        _api_keys=frozenset({FAKE_API_KEY}),
    )
    client = TestClient(create_app(cfg))
    client.post(
        "/run",
        json={
            "request_id": "api-audit-1",
            "user_id": "user-1",
            "session_id": "sess-1",
            "tenant_id": "tenant-a",
            "user_message": "read",
            "scenario": "safe_read",
        },
        headers={"X-API-Key": "lab-fake-wrong-key"},
    )
    raw = (tmp_path / "audit" / "api_events.jsonl").read_text(encoding="utf-8")
    assert "api_auth_failure" in raw
    assert FAKE_API_KEY not in raw
    assert "lab-fake-wrong-key" not in raw


def test_adapter_failure_audit_does_not_log_prompt_or_secrets(
    policy_path: Path,
    tmp_path: Path,
) -> None:
    secret_message = f"ignore {FAKE_SECRET}"
    request = AgentRequest(
        request_id="adapter-audit-1",
        correlation_id="corr-adapter-1",
        user_id="user-1",
        session_id="sess-1",
        tenant_id="tenant-a",
        role="user",
        user_message=secret_message,
        scenario="safe_read",
    )
    audit = AuditLogger(tmp_path / "audit.jsonl")
    pipeline = ControlPlanePipeline(
        policy_path,
        audit,
        llm_adapter=create_llm_adapter(mode=LLMAdapterMode.DISABLED_EXTERNAL),
    )
    with pytest.raises(LLMAdapterError):
        pipeline.run_protected(request)
    raw = audit.path.read_text(encoding="utf-8")
    events = audit.read_events()
    assert any(e["event_type"] == "adapter_failure" for e in events)
    assert FAKE_SECRET not in raw
    assert secret_message not in raw


def test_correlation_id_stable_across_request_flow(
    pipeline: ControlPlanePipeline,
    correlation_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(correlation_request)
    correlation_ids = {e["correlation_id"] for e in audit_logger.read_events()}
    assert correlation_ids == {"corr-session-abc"}


def test_correlation_id_defaults_to_request_id(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request)
    for event in audit_logger.read_events():
        assert event["correlation_id"] == base_request.request_id


def test_resolve_correlation_id_helper(correlation_request: AgentRequest) -> None:
    assert resolve_correlation_id(correlation_request) == "corr-session-abc"


def test_normalize_correlation_id_bounds_length() -> None:
    long_id = "x" * 200
    result = normalize_correlation_id(long_id, fallback="fb")
    assert len(result) == 128


def test_request_body_limit_audit_event(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from agent_control_plane.api import create_app
    from agent_control_plane.config import AppConfig, EnvironmentMode
    from agent_control_plane.llm_adapter import LLMAdapterMode

    policy_path = Path(__file__).resolve().parents[1] / "policies" / "default.yaml"
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
        llm_adapter_mode=LLMAdapterMode.SIMULATED,
        allow_live_llm_calls=False,
        llm_provider_name=None,
        llm_model_name=None,
        policy_path=policy_path,
        _api_keys=frozenset({FAKE_API_KEY}),
    )
    client = TestClient(create_app(cfg))
    client.post(
        "/run",
        json={
            "request_id": "body-limit-1",
            "user_id": "u",
            "session_id": "s",
            "tenant_id": "tenant-a",
            "user_message": "x",
            "scenario": "safe_read",
        },
        headers={
            "X-API-Key": FAKE_API_KEY,
            "Content-Length": "9999",
            "Content-Type": "application/json",
        },
        content=b"{}",
    )
    events = AuditLogger(tmp_path / "audit" / "api_events.jsonl").read_events()
    assert any(e["event_type"] == "request_body_limit_blocked" for e in events)


def test_taxonomy_event_types_present_in_pipeline(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    scenarios: list[tuple[str, str]] = [
        ("safe_read", "tool_allowed"),
        ("shell_attempt", "tool_blocked"),
        ("invalid_schema", "schema_validation_failed"),
        ("output_secret_leak", "output_filter_blocked"),
        ("cross_tenant_read", "cross_tenant_blocked"),
        ("injection_send_email", "provenance_denied"),
    ]
    for scenario, expected_type in scenarios:
        audit_logger.path.write_text("", encoding="utf-8")
        pipeline.run_protected(base_request.model_copy(update={"scenario": scenario}))
        types = {e["event_type"] for e in audit_logger.read_events()}
        assert expected_type in types, f"expected {expected_type} for {scenario}"
