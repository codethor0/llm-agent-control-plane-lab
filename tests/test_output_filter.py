"""Layered output filter blocks sensitive model text and structured leaks."""

import base64
import json

from agent_control_plane.audit_logger import AuditEvent, AuditLogger
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    RetrievedChunk,
    ToolOutputSegment,
)
from agent_control_plane.output_filter import (
    OutputDestination,
    OutputFilterContext,
    SourceSensitivity,
    build_filter_context_from_request,
    filter_model_output,
    filter_output,
    findings_for_audit,
)


def test_clean_output_allowed() -> None:
    result = filter_model_output("Here are your records for today.")
    assert result.allowed is True
    assert result.filtered_text
    assert result.finding_count == 0


def test_secret_pattern_blocked() -> None:
    result = filter_model_output("key: sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789")
    assert result.allowed is False
    assert result.reason == "secret_pattern_blocked"
    assert result.finding_count >= 1
    assert "secret_pattern" in result.finding_types


def test_private_key_blocked() -> None:
    text = "-----BEGIN PRIVATE KEY-----\nMIIE\n-----END PRIVATE KEY-----"
    result = filter_model_output(text)
    assert result.allowed is False
    assert result.reason == "private_key_material_blocked"


def test_jwt_like_token_blocked() -> None:
    jwt_like = (
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    result = filter_model_output(f"bearer={jwt_like}")
    assert result.allowed is False
    assert result.reason == "jwt_like_token_blocked"


def test_encoded_blob_blocked() -> None:
    payload = b"SensitiveExportData-" * 5
    blob = base64.b64encode(payload).decode()
    result = filter_model_output(f"data: {blob}")
    assert result.allowed is False
    assert result.reason == "encoded_blob_blocked"


def test_entropy_finding_blocks_high_entropy_token() -> None:
    # Lab-only fake high-entropy token (not a real secret).
    token = "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7"
    result = filter_output(
        f"payload={token}",
        OutputFilterContext(destination=OutputDestination.INTERNAL_DISPLAY),
    )
    assert result.allowed is False
    assert result.reason == "high_entropy_string_blocked"
    assert any(f.finding_type == "high_entropy_string" for f in result.findings)


def test_entropy_allows_normal_short_strings() -> None:
    result = filter_output(
        "status ok for tenant-a",
        OutputFilterContext(tenant_id="tenant-a"),
    )
    assert result.allowed is True


def test_structured_findings_returned_with_redacted_samples() -> None:
    result = filter_model_output("password=lab-fake-value")
    assert result.allowed is False
    assert result.findings
    sample = result.findings[0].redacted_sample
    assert "REDACTED" in sample
    assert "lab-fake-value" not in sample


def test_same_tenant_marker_allowed() -> None:
    result = filter_output(
        "summary for tenant_id:tenant-a",
        OutputFilterContext(tenant_id="tenant-a"),
    )
    assert result.allowed is True


def test_cross_tenant_output_blocked() -> None:
    result = filter_output(
        "record tenant_id:tenant-b exported",
        OutputFilterContext(tenant_id="tenant-a"),
    )
    assert result.allowed is False
    assert result.reason == "cross_tenant_output_blocked"
    assert any(f.finding_type == "cross_tenant_content" for f in result.findings)


def test_external_email_blocks_sensitive_classification() -> None:
    result = filter_output(
        "report classification:sensitive for review",
        OutputFilterContext(
            tenant_id="tenant-a",
            destination=OutputDestination.EXTERNAL_EMAIL,
        ),
    )
    assert result.allowed is False


def test_external_export_blocks_sensitive_findings() -> None:
    result = filter_output(
        "password=lab-fake-export-test",
        OutputFilterContext(destination=OutputDestination.EXTERNAL_EXPORT),
    )
    assert result.allowed is False


def test_internal_display_allows_benign_text() -> None:
    result = filter_output(
        "notes for internal display only",
        OutputFilterContext(destination=OutputDestination.INTERNAL_DISPLAY),
    )
    assert result.allowed is True


def test_audit_log_destination_does_not_return_raw_text() -> None:
    result = filter_output(
        "password=lab-fake-audit-test",
        OutputFilterContext(destination=OutputDestination.AUDIT_LOG),
    )
    assert result.filtered_text == ""
    assert result.findings


def test_allowlisted_schema_passes() -> None:
    ctx = OutputFilterContext(
        strict_response_schema=True,
        allowed_response_keys={"status", "record_count"},
    )
    result = filter_output(
        "",
        ctx,
        structured_output={"status": "ok", "record_count": 3},
    )
    assert result.allowed is True


def test_unknown_schema_key_blocks_in_strict_mode() -> None:
    ctx = OutputFilterContext(
        strict_response_schema=True,
        allowed_response_keys={"status"},
    )
    result = filter_output(
        "",
        ctx,
        structured_output={"status": "ok", "debug_blob": "x"},
    )
    assert result.allowed is False
    assert result.reason == "unknown_response_key_blocked"


def test_sensitive_schema_key_blocks_even_when_allowed_keys_match() -> None:
    ctx = OutputFilterContext(
        strict_response_schema=True,
        allowed_response_keys={"status", "password"},
    )
    result = filter_output(
        "",
        ctx,
        structured_output={"status": "ok", "password": "lab-fake"},
    )
    assert result.allowed is False
    assert result.reason == "sensitive_response_key_blocked"


def test_sensitive_source_blocks_external_destination(
    base_request: AgentRequest,
) -> None:
    request = base_request.model_copy(
        update={
            "retrieved_chunks": [
                RetrievedChunk(
                    id="c1",
                    content="classification:sensitive customer notes",
                    trust=ContextTrust.UNTRUSTED,
                    tenant_id="tenant-a",
                )
            ],
        }
    )
    ctx = build_filter_context_from_request(
        request,
        destination=OutputDestination.EXTERNAL_EMAIL,
    )
    assert ctx.source_sensitivity == SourceSensitivity.SENSITIVE
    result = filter_output("safe summary text only", ctx)
    assert result.allowed is False
    assert result.reason == "sensitive_source_external_destination_blocked"


def test_tool_output_source_blocks_external_destination(
    base_request: AgentRequest,
) -> None:
    request = base_request.model_copy(
        update={
            "tool_output_segments": [
                ToolOutputSegment(
                    execution_id="exec-1",
                    tool_name="read_records",
                    content="prior tool output",
                    trust=ContextTrust.UNTRUSTED,
                )
            ],
        }
    )
    ctx = build_filter_context_from_request(
        request,
        destination=OutputDestination.WEBHOOK,
    )
    result = filter_output("forwarding webhook payload", ctx)
    assert result.allowed is False
    assert result.reason == "tool_output_external_destination_blocked"


def test_internal_reviewed_source_can_pass_internal_display(
    base_request: AgentRequest,
) -> None:
    request = base_request.model_copy(
        update={
            "retrieved_chunks": [
                RetrievedChunk(
                    id="c1",
                    content="reviewed internal summary",
                    trust=ContextTrust.TRUSTED,
                    tenant_id="tenant-a",
                )
            ],
        }
    )
    ctx = build_filter_context_from_request(
        request,
        destination=OutputDestination.INTERNAL_DISPLAY,
    )
    result = filter_output("displaying reviewed summary", ctx)
    assert result.allowed is True


def test_findings_for_audit_contains_redacted_only() -> None:
    result = filter_model_output("password=lab-fake-audit-metadata")
    serialized = findings_for_audit(result.findings)
    assert serialized
    blob = json.dumps(serialized)
    assert "lab-fake-audit-metadata" not in blob
    assert all("redacted_sample" in item for item in serialized)


def test_audit_logger_stores_output_filter_metadata(tmp_path: object) -> None:
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    logger = AuditLogger(tmp_path / "audit.jsonl")
    logger.write(
        AuditEvent(
            event_type="output_filter_blocked",
            correlation_id="req-1",
            request_id="req-1",
            user_id="user-1",
            session_id="sess-1",
            tenant_id="tenant-a",
            model="simulated-v1",
            tool_name=None,
            target=None,
            risk_level=None,
            source_context_ids=[],
            retrieved_context_trust=None,
            policy_decision="deny",
            policy_reason="secret_pattern_blocked",
            contains_sensitive_data=True,
            human_approval_required=False,
            stage="output_filter",
            allowed=False,
            output_filter_decision="block",
            output_finding_count=1,
            output_finding_types=["secret_pattern"],
            output_highest_severity="critical",
            output_findings_redacted=[
                {
                    "finding_type": "secret_pattern",
                    "severity": "critical",
                    "reason": "secret_pattern_blocked",
                    "redacted_sample": "pass...[REDACTED]",
                    "rule_id": "pattern.secret",
                }
            ],
        )
    )
    events = logger.read_events()
    assert events[0]["output_filter_decision"] == "block"
    assert events[0]["output_finding_count"] == 1
    assert "sk-live" not in json.dumps(events)


def test_pipeline_output_filter_audit_has_safe_metadata(
    pipeline: object,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    from agent_control_plane.pipeline import ControlPlanePipeline

    assert isinstance(pipeline, ControlPlanePipeline)
    pipeline.run_protected(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    events = audit_logger.read_events()
    blocked = [e for e in events if e["event_type"] == "output_filter_blocked"]
    assert blocked
    event = blocked[0]
    assert event["output_filter_decision"] == "block"
    assert event["output_finding_count"] >= 1
    raw = audit_logger.path.read_text(encoding="utf-8")
    assert "sk-live-FAKE" not in raw
