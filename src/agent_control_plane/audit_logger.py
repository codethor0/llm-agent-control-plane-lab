"""Structured JSONL audit logging with redaction."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REDACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[a-zA-Z0-9_-]{8,}"),
    re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END"),
]


@dataclass
class AuditEvent:
    """Fields required for audit events per project doctrine."""

    event_type: str
    request_id: str
    user_id: str
    session_id: str
    tenant_id: str
    model: str
    tool_name: str | None
    target: str | None
    risk_level: str | None
    source_context_ids: list[str]
    retrieved_context_trust: str | None
    policy_decision: str
    policy_reason: str
    contains_sensitive_data: bool
    human_approval_required: bool
    stage: str
    allowed: bool
    approval_id: str | None = None
    approver_id: str | None = None
    approval_decision: str | None = None
    approval_reason: str | None = None
    approval_token_valid: bool | None = None
    approval_token_failure_reason: str | None = None


class AuditLogger:
    """
    Append-only JSONL audit logger.

    Invariant: raw secrets, tokens, passwords, and private keys are never persisted.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def write(self, event: AuditEvent) -> None:
        """Append a redacted audit event as one JSONL line."""
        record = {
            "event_type": event.event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": event.request_id,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "tenant_id": event.tenant_id,
            "model": event.model,
            "tool_name": event.tool_name,
            "target": event.target,
            "risk_level": event.risk_level,
            "source_context_ids": event.source_context_ids,
            "retrieved_context_trust": event.retrieved_context_trust,
            "policy_decision": event.policy_decision,
            "policy_reason": _redact(event.policy_reason),
            "contains_sensitive_data": event.contains_sensitive_data,
            "human_approval_required": event.human_approval_required,
            "stage": event.stage,
            "allowed": event.allowed,
            "approval_id": event.approval_id,
            "approver_id": event.approver_id,
            "approval_decision": event.approval_decision,
            "approval_reason": _redact(event.approval_reason) if event.approval_reason else None,
            "approval_token_valid": event.approval_token_valid,
            "approval_token_failure_reason": event.approval_token_failure_reason,
        }
        line = json.dumps(record, separators=(",", ":"))
        safe_line = _redact(line)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(safe_line + "\n")

    def read_events(self) -> list[dict[str, Any]]:
        """Read all events (for tests)."""
        if not self._path.is_file():
            return []
        events: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events


def _redact(value: str) -> str:
    redacted = value
    for pattern in _REDACT_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
