"""Lab-only approval tokens bound to a specific tool action fingerprint."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from agent_control_plane.models import AgentRequest, Provenance, ToolCallPayload
from agent_control_plane.policy_types import ToolPolicy
from agent_control_plane.provenance_integrity import (
    canonicalize_provenance as _canonicalize_provenance,
)

_USED_APPROVAL_IDS: set[str] = set()


class ApprovalRequestFingerprint(BaseModel):
    """Deterministic binding material for a single tool authorization request."""

    user_id: str
    tenant_id: str
    tool_name: str
    target: str | None
    action: str
    risk_level: str
    source_context_ids: list[str] = Field(default_factory=list)
    provenance_fingerprint: str
    action_fingerprint: str


class ApprovalToken(BaseModel):
    """Human approval bound to one lab action fingerprint (not production IAM)."""

    approval_id: str
    approver_id: str
    approved_at: str
    expires_at: str
    one_time_use: bool = True
    used: bool = False
    user_id: str
    tenant_id: str
    tool_name: str
    target: str | None
    action: str
    risk_level: str
    source_context_ids: list[str] = Field(default_factory=list)
    provenance_fingerprint: str
    action_fingerprint: str
    approval_reason: str = ""


def clear_used_approval_tokens() -> None:
    """Reset one-time-use registry (tests only)."""
    _USED_APPROVAL_IDS.clear()


def compute_provenance_fingerprint(provenance: Provenance | None) -> str:
    """SHA-256 hex of canonical provenance metadata (no raw content)."""
    if provenance is None:
        payload: dict[str, Any] = {"provenance": None}
    else:
        payload = _canonicalize_provenance(provenance)
    return _sha256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _canonical_action_payload(
    request: AgentRequest,
    tool_call: ToolCallPayload,
    risk_level: str,
) -> dict[str, Any]:
    provenance = tool_call.provenance
    return {
        "user_id": request.user_id,
        "tenant_id": request.tenant_id,
        "tool_name": tool_call.tool_name,
        "target": tool_call.target,
        "action": _action_label(tool_call),
        "risk_level": risk_level,
        "source_context_ids": sorted(provenance.context_ids) if provenance else [],
        "provenance_fingerprint": compute_provenance_fingerprint(provenance),
    }


def _action_label(tool_call: ToolCallPayload) -> str:
    return json.dumps(
        {"tool_name": tool_call.tool_name, "arguments": tool_call.arguments},
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_action_fingerprint(
    request: AgentRequest,
    tool_call: ToolCallPayload,
    risk_level: str,
) -> str:
    """Return deterministic SHA-256 hex for the full approval binding."""
    return _sha256_hex(
        json.dumps(_canonical_action_payload(request, tool_call, risk_level), sort_keys=True)
    )


def build_approval_fingerprint(
    request: AgentRequest,
    tool_call: ToolCallPayload,
    risk_level: str,
) -> ApprovalRequestFingerprint:
    """Build fingerprint object for inspection and token creation."""
    payload = _canonical_action_payload(request, tool_call, risk_level)
    action_fp = _sha256_hex(json.dumps(payload, sort_keys=True))
    return ApprovalRequestFingerprint(
        user_id=payload["user_id"],
        tenant_id=payload["tenant_id"],
        tool_name=payload["tool_name"],
        target=payload["target"],
        action=payload["action"],
        risk_level=payload["risk_level"],
        source_context_ids=payload["source_context_ids"],
        provenance_fingerprint=payload["provenance_fingerprint"],
        action_fingerprint=action_fp,
    )


def create_approval_token(
    approver_id: str,
    request: AgentRequest,
    tool_call: ToolCallPayload,
    tool_policy: ToolPolicy,
    *,
    approval_reason: str = "lab_simulated_approval",
    ttl_seconds: int = 3600,
    approved_at: datetime | None = None,
) -> ApprovalToken:
    """Mint a lab approval token bound to the current request and tool call."""
    now = approved_at or datetime.now(UTC)
    risk_level = tool_policy.risk_level.value
    fingerprint = build_approval_fingerprint(request, tool_call, risk_level)
    return ApprovalToken(
        approval_id=f"apr-{uuid.uuid4().hex}",
        approver_id=approver_id,
        approved_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
        one_time_use=True,
        used=False,
        user_id=fingerprint.user_id,
        tenant_id=fingerprint.tenant_id,
        tool_name=fingerprint.tool_name,
        target=fingerprint.target,
        action=fingerprint.action,
        risk_level=fingerprint.risk_level,
        source_context_ids=fingerprint.source_context_ids,
        provenance_fingerprint=fingerprint.provenance_fingerprint,
        action_fingerprint=fingerprint.action_fingerprint,
        approval_reason=approval_reason,
    )


def is_approval_token_expired(
    token: ApprovalToken,
    now: datetime | None = None,
) -> bool:
    """Return True when the token is past expires_at."""
    current = now or datetime.now(UTC)
    expires = datetime.fromisoformat(token.expires_at)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    return current > expires


def mark_approval_token_used(approval_id: str) -> None:
    """Record one-time use for a lab approval token."""
    _USED_APPROVAL_IDS.add(approval_id)


def is_approval_token_used(approval_id: str) -> bool:
    """Return True if the approval_id was already consumed in this process."""
    return approval_id in _USED_APPROVAL_IDS


def verify_approval_token(
    token: ApprovalToken,
    request: AgentRequest,
    tool_call: ToolCallPayload,
    risk_level: str,
    *,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """
    Verify token binding to the current request.

    Invariant: valid token does not authorize by itself; broker policy still applies.
    """
    if token.used or is_approval_token_used(token.approval_id):
        return False, "approval_token_reused"

    if is_approval_token_expired(token, now=now):
        return False, "approval_token_expired"

    if token.user_id != request.user_id:
        return False, "approval_token_user_mismatch"

    if token.tenant_id != request.tenant_id:
        return False, "approval_token_tenant_mismatch"

    if token.tool_name != tool_call.tool_name:
        return False, "approval_token_tool_mismatch"

    if token.target != tool_call.target:
        return False, "approval_token_target_mismatch"

    if token.risk_level != risk_level:
        return False, "approval_token_risk_mismatch"

    provenance = tool_call.provenance
    context_ids = sorted(provenance.context_ids) if provenance else []
    if token.source_context_ids != context_ids:
        return False, "approval_token_context_mismatch"

    current_provenance_fp = compute_provenance_fingerprint(provenance)
    if token.provenance_fingerprint != current_provenance_fp:
        return False, "approval_token_provenance_mismatch"

    current_action_fp = compute_action_fingerprint(request, tool_call, risk_level)
    if token.action_fingerprint != current_action_fp:
        return False, "approval_token_action_mismatch"

    return True, "approval_token_valid"


def _rebuild_agent_request_model() -> None:
    from agent_control_plane import models

    models.AgentRequest.model_rebuild(
        _types_namespace={"ApprovalToken": ApprovalToken},
    )


_rebuild_agent_request_model()
