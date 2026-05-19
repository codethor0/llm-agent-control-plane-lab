"""Operational observability helpers: correlation IDs and API audit events."""

from __future__ import annotations

from agent_control_plane.audit_logger import AuditEvent, AuditLogger
from agent_control_plane.models import AgentRequest

MAX_CORRELATION_ID_LEN = 128


def normalize_correlation_id(value: str | None, *, fallback: str) -> str:
    """
    Return a bounded correlation identifier.

    Invariant: never returns empty string; does not log or persist secrets.
    """
    if value is None or not value.strip():
        return fallback
    trimmed = value.strip()
    if len(trimmed) > MAX_CORRELATION_ID_LEN:
        return trimmed[:MAX_CORRELATION_ID_LEN]
    return trimmed


def resolve_correlation_id(request: AgentRequest) -> str:
    """Stable correlation ID for all audit events in one agent turn."""
    return normalize_correlation_id(request.correlation_id, fallback=request.request_id)


def write_operational_audit(
    logger: AuditLogger,
    *,
    event_type: str,
    correlation_id: str,
    request_id: str,
    stage: str,
    policy_reason: str,
    allowed: bool = False,
    user_id: str = "unknown",
    session_id: str = "unknown",
    tenant_id: str = "unknown",
    tool_name: str | None = None,
    target: str | None = None,
) -> None:
    """Write a minimal operational audit event (API boundary, adapter failure)."""
    logger.write(
        AuditEvent(
            event_type=event_type,
            correlation_id=correlation_id,
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            model="n/a",
            tool_name=tool_name,
            target=target,
            risk_level=None,
            source_context_ids=[],
            retrieved_context_trust=None,
            policy_decision="deny" if not allowed else "allow",
            policy_reason=policy_reason,
            contains_sensitive_data=False,
            human_approval_required=False,
            stage=stage,
            allowed=allowed,
        )
    )
