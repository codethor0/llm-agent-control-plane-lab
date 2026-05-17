"""Property-based tests for approval token binding."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import assume, given
from tests.property_helpers import context_ids, safe_identifier, tenant_id

from agent_control_plane.approval_tokens import (
    clear_used_approval_tokens,
    create_approval_token,
    mark_approval_token_used,
    verify_approval_token,
)
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.policy_types import ToolPolicy

_EMAIL_POLICY = ToolPolicy.model_validate(
    {
        "enabled": True,
        "risk_level": "high",
        "external_effect": True,
        "destructive": False,
        "requires_human_approval": True,
        "allowed_roles": ["user", "admin"],
    }
)


def _request(tenant: str, user: str = "user-prop") -> AgentRequest:
    return AgentRequest(
        request_id="req-apr-prop",
        user_id=user,
        session_id="sess-apr",
        tenant_id=tenant,
        role="user",
        user_message="Approval property test.",
    )


def _email_tool(tenant: str, ctx: list[str]) -> ToolCallPayload:
    return ToolCallPayload(
        tool_name="send_email",
        arguments={"to": "user@example.invalid", "subject": "Lab", "body": "Fake"},
        target=tenant,
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=ctx,
        ),
    )


@given(tenant_id, context_ids)
def test_property_valid_token_verifies(tenant: str, ctx: list[str]) -> None:
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    ok, reason = verify_approval_token(token, request, tool, "high")
    assert ok is True
    assert reason == "approval_token_valid"


@given(tenant_id, context_ids, safe_identifier)
def test_property_tool_mismatch_rejected(tenant: str, ctx: list[str], other: str) -> None:
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    other_tool = tool.model_copy(update={"tool_name": f"tool_{other}"})
    ok, reason = verify_approval_token(token, request, other_tool, "high")
    assert ok is False
    assert reason == "approval_token_tool_mismatch"


@given(tenant_id, context_ids, tenant_id)
def test_property_tenant_mismatch_rejected(tenant: str, ctx: list[str], other: str) -> None:
    assume(tenant != other)
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    ok, reason = verify_approval_token(token, _request(other), tool, "high")
    assert ok is False
    assert reason == "approval_token_tenant_mismatch"


@given(tenant_id, context_ids, safe_identifier)
def test_property_user_mismatch_rejected(tenant: str, ctx: list[str], other_user: str) -> None:
    assume(other_user != "user-prop")
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    ok, reason = verify_approval_token(token, _request(tenant, other_user), tool, "high")
    assert ok is False
    assert reason == "approval_token_user_mismatch"


@given(tenant_id, context_ids)
def test_property_risk_mismatch_rejected(tenant: str, ctx: list[str]) -> None:
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    ok, reason = verify_approval_token(token, request, tool, "low")
    assert ok is False
    assert reason == "approval_token_risk_mismatch"


@given(tenant_id, context_ids, context_ids)
def test_property_context_mismatch_rejected(
    tenant: str,
    ctx: list[str],
    other_ctx: list[str],
) -> None:
    assume(ctx != other_ctx)
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    other_tool = tool.model_copy(
        update={
            "provenance": Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=other_ctx,
            )
        }
    )
    ok, reason = verify_approval_token(token, request, other_tool, "high")
    assert ok is False
    assert reason == "approval_token_context_mismatch"


@given(tenant_id, context_ids)
def test_property_reused_token_rejected(tenant: str, ctx: list[str]) -> None:
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    mark_approval_token_used(token.approval_id)
    ok, reason = verify_approval_token(token, request, tool, "high")
    assert ok is False
    assert reason == "approval_token_reused"


@given(tenant_id, context_ids, tenant_id)
def test_property_target_mismatch_rejected(tenant: str, ctx: list[str], other: str) -> None:
    assume(other != tenant)
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    token = create_approval_token("approver-prop", request, tool, _EMAIL_POLICY)
    other_tool = tool.model_copy(update={"target": other})
    ok, reason = verify_approval_token(token, request, other_tool, "high")
    assert ok is False
    assert reason == "approval_token_target_mismatch"


@given(tenant_id, context_ids)
def test_property_expired_token_rejected(tenant: str, ctx: list[str]) -> None:
    clear_used_approval_tokens()
    request = _request(tenant)
    tool = _email_tool(tenant, ctx)
    past = datetime.now(UTC) - timedelta(hours=2)
    token = create_approval_token(
        "approver-prop",
        request,
        tool,
        _EMAIL_POLICY,
        ttl_seconds=60,
        approved_at=past,
    )
    ok, reason = verify_approval_token(token, request, tool, "high")
    assert ok is False
    assert reason == "approval_token_expired"
