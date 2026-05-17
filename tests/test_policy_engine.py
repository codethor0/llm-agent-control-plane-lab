"""Policy engine deny-by-default and tool rules."""

from pathlib import Path

from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.policy_engine import evaluate_policy, load_policy


def _request(**kwargs: object) -> AgentRequest:
    base = {
        "request_id": "r",
        "user_id": "u",
        "session_id": "s",
        "tenant_id": "tenant-a",
        "role": "user",
        "human_approval": False,
        "user_message": "x",
    }
    base.update(kwargs)
    return AgentRequest.model_validate(base)


def _tool(**kwargs: object) -> ToolCallPayload:
    base = {
        "tool_name": "read_records",
        "arguments": {"record_ids": ["1"]},
        "target": "tenant-a",
        "provenance": Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    }
    base.update(kwargs)
    return ToolCallPayload.model_validate(base)


def test_policy_defaults_to_deny_for_unknown_tool(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        _request(),
        _tool(tool_name="unknown_tool_xyz"),
    )
    assert decision.allowed is False
    assert decision.reason == "unknown_tool_denied_by_policy"


def test_run_shell_disabled_by_policy(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy, _request(role="admin", human_approval=True), _tool(tool_name="run_shell")
    )
    assert decision.allowed is False
    assert decision.reason == "tool_disabled_by_policy"


def test_missing_provenance_blocks_execution(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(policy, _request(), _tool(provenance=None))
    assert decision.allowed is False
    assert decision.reason == "missing_provenance_denied"


def test_cross_tenant_target_denied(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(policy, _request(), _tool(target="tenant-b"))
    assert decision.allowed is False
    assert decision.reason == "cross_tenant_target_denied"


def test_untrusted_retrieved_cannot_authorize_external_effect(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        _request(human_approval=True),
        _tool(
            tool_name="send_email",
            arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
            provenance=Provenance(
                source=ProvenanceSource.RETRIEVED,
                trust=ContextTrust.UNTRUSTED,
                context_ids=["rag"],
            ),
        ),
    )
    assert decision.allowed is False
    assert decision.reason == "retrieved_cannot_authorize_tool_execution"


def test_export_records_requires_admin_role(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        _request(role="user", human_approval=True),
        _tool(
            tool_name="export_records",
            arguments={"format": "json"},
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is False
    assert decision.reason == "role_not_permitted_for_tool"


def test_export_records_allowed_for_admin_with_approval(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        _request(role="admin", human_approval=True),
        _tool(
            tool_name="export_records",
            arguments={"format": "json"},
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is True


def test_read_records_allowed_for_user(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(policy, _request(), _tool())
    assert decision.allowed is True
