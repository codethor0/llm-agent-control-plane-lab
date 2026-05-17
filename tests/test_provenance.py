"""Provenance authorization tests (declarative metadata)."""

from pathlib import Path

from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.policy_engine import evaluate_policy, load_policy
from agent_control_plane.policy_types import ToolPolicy
from agent_control_plane.provenance import validate_provenance_for_tool


def _tool_policy(**kwargs: object) -> ToolPolicy:
    return ToolPolicy.model_validate(
        {
            "enabled": True,
            "risk_level": "low",
            "external_effect": False,
            "destructive": False,
            "requires_human_approval": False,
            "allowed_roles": ["user"],
            **kwargs,
        }
    )


def test_missing_provenance_blocks_tool_calls() -> None:
    ok, reason = validate_provenance_for_tool(_tool_policy(), None)
    assert ok is False
    assert reason == "missing_provenance_denied"


def test_user_generated_cannot_authorize_external_effects() -> None:
    ok, reason = validate_provenance_for_tool(
        _tool_policy(external_effect=True),
        Provenance(
            source=ProvenanceSource.USER,
            trust=ContextTrust.TRUSTED,
            context_ids=["u1"],
        ),
    )
    assert ok is False
    assert reason == "user_cannot_authorize_tool_execution"


def test_web_context_cannot_authorize_external_effects() -> None:
    ok, reason = validate_provenance_for_tool(
        _tool_policy(external_effect=True),
        Provenance(
            source=ProvenanceSource.WEB,
            trust=ContextTrust.TRUSTED,
            context_ids=["w1"],
        ),
    )
    assert ok is False
    assert reason == "web_cannot_authorize_tool_execution"


def test_email_context_cannot_authorize_external_effects() -> None:
    ok, reason = validate_provenance_for_tool(
        _tool_policy(external_effect=True),
        Provenance(
            source=ProvenanceSource.EMAIL,
            trust=ContextTrust.TRUSTED,
            context_ids=["e1"],
        ),
    )
    assert ok is False
    assert reason == "email_cannot_authorize_tool_execution"


def test_support_ticket_cannot_authorize_external_effects() -> None:
    ok, reason = validate_provenance_for_tool(
        _tool_policy(external_effect=True),
        Provenance(
            source=ProvenanceSource.SUPPORT_TICKET,
            trust=ContextTrust.TRUSTED,
            context_ids=["t1"],
        ),
    )
    assert ok is False
    assert reason == "support_ticket_cannot_authorize_tool_execution"


def test_internal_reviewed_allows_safe_internal_read() -> None:
    ok, reason = validate_provenance_for_tool(
        _tool_policy(external_effect=False, destructive=False),
        Provenance(
            source=ProvenanceSource.INTERNAL_REVIEWED,
            trust=ContextTrust.TRUSTED,
            context_ids=["review-1"],
        ),
    )
    assert ok is True
    assert reason == "internal_reviewed_provenance_allowed"


def test_internal_reviewed_cannot_authorize_export(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="admin",
            human_approval=True,
            user_message="x",
        ),
        ToolCallPayload(
            tool_name="export_records",
            arguments={"format": "json"},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.INTERNAL_REVIEWED,
                trust=ContextTrust.TRUSTED,
                context_ids=["review-1"],
            ),
        ),
    )
    assert decision.allowed is False
    assert decision.reason == "internal_reviewed_cannot_authorize_external_or_destructive"


def test_tenant_mismatch_blocks_execution(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="user",
            user_message="x",
        ),
        ToolCallPayload(
            tool_name="read_records",
            arguments={"record_ids": ["1"]},
            target="tenant-b",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is False
    assert decision.reason == "cross_tenant_target_denied"
