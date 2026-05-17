"""Audit logger writes structured JSONL without raw secrets."""

from agent_control_plane.audit_logger import AuditEvent, AuditLogger


def test_audit_event_fields_written(tmp_path: object, audit_logger: AuditLogger) -> None:
    audit_logger.write(
        AuditEvent(
            event_type="tool_blocked",
            request_id="req-1",
            user_id="user-1",
            session_id="sess-1",
            tenant_id="tenant-a",
            model="simulated-v1",
            tool_name="send_email",
            target="tenant-a",
            risk_level="high",
            source_context_ids=["ctx-1"],
            retrieved_context_trust="untrusted",
            policy_decision="deny",
            policy_reason="human_approval_required_by_policy",
            contains_sensitive_data=False,
            human_approval_required=True,
            stage="tool_broker",
            allowed=False,
        )
    )
    events = audit_logger.read_events()
    assert len(events) == 1
    event = events[0]
    assert event["event_type"] == "tool_blocked"
    assert event["request_id"] == "req-1"
    assert event["policy_decision"] == "deny"
    assert "timestamp" in event


def test_audit_redacts_secrets_in_reason(audit_logger: AuditLogger) -> None:
    audit_logger.write(
        AuditEvent(
            event_type="output_filter_blocked",
            request_id="req-2",
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
            policy_reason="matched sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789",
            contains_sensitive_data=True,
            human_approval_required=False,
            stage="output_filter",
            allowed=False,
        )
    )
    raw = audit_logger.path.read_text(encoding="utf-8")
    assert "sk-live-FAKE" not in raw
    assert "[REDACTED]" in raw
