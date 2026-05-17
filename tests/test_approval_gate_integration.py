"""Approval gate wired through tool broker and protected pipeline."""

from pathlib import Path

from agent_control_plane.approval_gate import evaluate_approval_gate
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.pipeline import ControlPlanePipeline
from agent_control_plane.policy_engine import load_policy
from agent_control_plane.policy_types import ToolPolicy
from agent_control_plane.tool_broker import broker_tool_request


def _email_policy() -> ToolPolicy:
    return ToolPolicy.model_validate(
        {
            "enabled": True,
            "risk_level": "high",
            "external_effect": True,
            "destructive": False,
            "requires_human_approval": True,
            "allowed_roles": ["user", "admin"],
        }
    )


def test_send_email_requires_human_approval_via_broker(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    request = AgentRequest(
        request_id="r",
        user_id="u",
        session_id="s",
        tenant_id="tenant-a",
        role="user",
        human_approval=False,
        user_message="x",
    )
    tool = ToolCallPayload(
        tool_name="send_email",
        arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    decision = broker_tool_request(request, policy, tool)
    assert decision.schema_valid is True
    assert decision.allowed is False
    assert "human_approval" in decision.reason


def test_send_email_allowed_with_human_approval(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    request = AgentRequest(
        request_id="r",
        user_id="u",
        session_id="s",
        tenant_id="tenant-a",
        role="user",
        human_approval=True,
        user_message="x",
    )
    tool = ToolCallPayload(
        tool_name="send_email",
        arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    decision = broker_tool_request(request, policy, tool)
    assert decision.allowed is True


def test_export_records_requires_admin_and_approval(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool = ToolCallPayload(
        tool_name="export_records",
        arguments={"format": "json"},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    denied_role = broker_tool_request(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="user",
            human_approval=True,
            user_message="x",
        ),
        policy,
        tool,
    )
    assert denied_role.allowed is False
    assert denied_role.reason == "role_not_permitted_for_tool"

    denied_approval = broker_tool_request(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="admin",
            human_approval=False,
            user_message="x",
        ),
        policy,
        tool,
    )
    assert denied_approval.allowed is False
    assert "human_approval" in denied_approval.reason


def test_high_impact_external_requires_approval() -> None:
    result = evaluate_approval_gate(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="t",
            role="user",
            human_approval=False,
            user_message="x",
        ),
        _email_policy(),
        ToolCallPayload(
            tool_name="send_email",
            arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
            target="t",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert result.approval_required is True
    assert result.allowed is False


def test_approval_without_policy_allow_is_impossible(policy_path: Path) -> None:
    """Approval alone cannot allow a disabled tool."""
    policy = load_policy(policy_path)
    tool = ToolCallPayload(
        tool_name="run_shell",
        arguments={"command": "id"},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    decision = broker_tool_request(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="admin",
            human_approval=True,
            user_message="x",
        ),
        policy,
        tool,
    )
    assert decision.allowed is False
    assert decision.reason == "tool_disabled_by_policy"


def test_protected_pipeline_send_email_blocked_without_approval(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
) -> None:
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "human_approval": False})
    )
    assert result.allowed is False
    assert "human_approval" in result.reason


def test_protected_pipeline_send_email_allowed_with_approval(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
) -> None:
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "human_approval": True})
    )
    assert result.allowed is True
    assert result.stage == "simulation"
