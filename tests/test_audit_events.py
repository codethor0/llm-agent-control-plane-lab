"""Audit event coverage for control plane decisions."""

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.models import AgentRequest
from agent_control_plane.pipeline import ControlPlanePipeline


def test_audit_allowed_tool_event(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "safe_read"}))
    events = audit_logger.read_events()
    assert any(e["event_type"] == "tool_allowed" and e["allowed"] is True for e in events)


def test_audit_blocked_tool_event(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    events = audit_logger.read_events()
    assert any(e["event_type"] == "tool_blocked" and e["allowed"] is False for e in events)


def test_audit_schema_validation_failure(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "invalid_schema"}))
    assert any(e["event_type"] == "schema_validation_failed" for e in audit_logger.read_events())


def test_audit_output_filter_failure(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    assert any(e["event_type"] == "output_filter_blocked" for e in audit_logger.read_events())


def test_audit_approval_denied(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(
        base_request.model_copy(update={"scenario": "export_no_approval", "role": "admin"})
    )
    events = audit_logger.read_events()
    assert any(
        e["event_type"] == "approval_denied" and e["human_approval_required"] is True
        for e in events
    )


def test_audit_cross_tenant_blocked(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "cross_tenant_read"}))
    assert any(e["event_type"] == "cross_tenant_blocked" for e in audit_logger.read_events())


def test_audit_provenance_denied(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "injection_send_email"}))
    assert any(e["event_type"] == "provenance_denied" for e in audit_logger.read_events())


def test_audit_no_raw_secrets_in_log(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    raw = audit_logger.path.read_text(encoding="utf-8")
    assert "sk-live-FAKE" not in raw
