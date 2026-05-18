"""Property-based tests for tool broker authorization boundaries."""

from __future__ import annotations

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from agent_control_plane.approval_tokens import clear_used_approval_tokens, create_approval_token
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.policy_engine import load_policy
from agent_control_plane.policy_types import PolicyDocument
from agent_control_plane.tool_broker import broker_tool_request
from tests.property_helpers import (
    TENANT_IDS,
    context_ids,
    non_authorizing_source,
    role,
    tenant_id,
    unknown_tool,
)

_POLICY: PolicyDocument | None = None


def _policy() -> PolicyDocument:
    global _POLICY
    if _POLICY is None:
        path = Path(__file__).resolve().parents[1] / "policies" / "default.yaml"
        _POLICY = load_policy(path)
    return _POLICY


def _request(tenant: str, user_role: str, *, human_approval: bool = False) -> AgentRequest:
    return AgentRequest(
        request_id="req-prop",
        user_id="user-prop",
        session_id="sess-prop",
        tenant_id=tenant,
        role=user_role,
        human_approval=human_approval,
        user_message="Property test message.",
    )


def _tool(
    tool_name: str,
    tenant: str,
    *,
    source: ProvenanceSource = ProvenanceSource.MODEL,
    trust: ContextTrust = ContextTrust.TRUSTED,
    ctx_ids: list[str] | None = None,
) -> ToolCallPayload:
    arguments: dict[str, object]
    if tool_name == "read_records":
        arguments = {"record_ids": ["r-prop"]}
    elif tool_name == "send_email":
        arguments = {"to": "user@example.invalid", "subject": "Lab", "body": "Fake"}
    elif tool_name == "export_records":
        arguments = {"format": "json"}
    elif tool_name == "delete_records":
        arguments = {"record_ids": ["r-prop"]}
    else:
        arguments = {"command": "echo lab-safe"}
    return ToolCallPayload(
        tool_name=tool_name,
        arguments=arguments,
        target=tenant,
        provenance=Provenance(
            source=source,
            trust=trust,
            context_ids=ctx_ids or ["ctx-prop"],
        ),
    )


@given(unknown_tool, tenant_id, role)
def test_property_unknown_tools_denied(tool_name: str, tenant: str, user_role: str) -> None:
    decision = broker_tool_request(_request(tenant, user_role), _policy(), _tool(tool_name, tenant))
    assert decision.allowed is False
    assert decision.schema_valid is False


@given(tenant_id, role)
def test_property_disabled_run_shell_denied(tenant: str, user_role: str) -> None:
    decision = broker_tool_request(
        _request(tenant, user_role, human_approval=True),
        _policy(),
        _tool("run_shell", tenant),
    )
    assert decision.allowed is False
    assert "disabled" in decision.reason or "run_shell" in decision.reason


@given(
    st.sampled_from(TENANT_IDS),
    st.sampled_from(TENANT_IDS),
)
def test_property_cross_tenant_target_denied(tenant: str, other_tenant: str) -> None:
    if other_tenant == tenant:
        return
    decision = broker_tool_request(
        _request(tenant, "user"),
        _policy(),
        _tool("read_records", other_tenant),
    )
    assert decision.allowed is False
    assert decision.reason == "cross_tenant_target_denied"


@given(tenant_id, non_authorizing_source, context_ids)
def test_property_non_authorizing_provenance_denied_for_send_email(
    tenant: str,
    source: ProvenanceSource,
    ctx_ids: list[str],
) -> None:
    decision = broker_tool_request(
        _request(tenant, "user", human_approval=True),
        _policy(),
        _tool("send_email", tenant, source=source, trust=ContextTrust.UNTRUSTED, ctx_ids=ctx_ids),
    )
    assert decision.allowed is False
    assert "cannot_authorize" in decision.reason or "provenance" in decision.reason


@given(tenant_id)
def test_property_missing_provenance_denied(tenant: str) -> None:
    tool = ToolCallPayload(
        tool_name="read_records",
        arguments={"record_ids": ["r-1"]},
        target=tenant,
        provenance=None,
    )
    decision = broker_tool_request(_request(tenant, "user"), _policy(), tool)
    assert decision.allowed is False
    assert decision.reason == "missing_provenance_denied"


@given(tenant_id)
def test_property_human_approval_does_not_bypass_disabled_shell(tenant: str) -> None:
    clear_used_approval_tokens()
    tool = _tool("run_shell", tenant)
    policy = _policy()
    token = create_approval_token(
        "approver-prop",
        _request(tenant, "admin", human_approval=True),
        tool,
        policy.tools["run_shell"],
    )
    request = _request(tenant, "admin", human_approval=True).model_copy(
        update={"approval_token": token}
    )
    decision = broker_tool_request(
        request,
        policy,
        tool,
        require_approval_token=True,
    )
    assert decision.allowed is False


@given(
    tenant_id,
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=40),
)
def test_property_random_free_text_not_executable(tenant: str, noise: str) -> None:
    """Generated free-form strings are not treated as tool names or permissions."""
    if not noise or " " in noise.strip():
        return
    if noise in {"read_records", "send_email", "run_shell"}:
        return
    decision = broker_tool_request(
        _request(tenant, "user"),
        _policy(),
        ToolCallPayload(
            tool_name=noise,
            arguments={},
            target=tenant,
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["n"],
            ),
        ),
    )
    assert decision.allowed is False
