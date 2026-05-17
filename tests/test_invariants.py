"""Explicit security invariant coverage (one concern per test)."""

from pathlib import Path

import pytest

from agent_control_plane.agent_core import run_simulated_agent
from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.output_filter import filter_model_output
from agent_control_plane.pipeline import ControlPlanePipeline
from agent_control_plane.policy_engine import evaluate_policy, load_policy
from agent_control_plane.schemas import validate_tool_arguments
from agent_control_plane.simulator import simulate_tool_execution
from agent_control_plane.tool_broker import broker_tool_request


def test_invariant_model_output_is_untrusted(base_request: AgentRequest) -> None:
    turn = run_simulated_agent(base_request)
    assert turn.natural_language
    assert turn.tool_call is not None


def test_invariant_free_form_text_not_executable(base_request: AgentRequest) -> None:
    turn = run_simulated_agent(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    assert turn.tool_call is None
    assert "sk-live" in turn.natural_language


def test_invariant_schema_validation_not_authorization(policy_path: Path) -> None:
    ok, _ = validate_tool_arguments(
        "send_email",
        {"to": "a@b.invalid", "subject": "s", "body": "b"},
    )
    assert ok is True
    policy = load_policy(policy_path)
    decision = broker_tool_request(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="user",
            human_approval=False,
            user_message="x",
        ),
        policy,
        ToolCallPayload(
            tool_name="send_email",
            arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is False


def test_invariant_tool_broker_is_authority_boundary(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = broker_tool_request(
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="user",
            user_message="x",
        ),
        policy,
        ToolCallPayload(
            tool_name="deploy_malware",
            arguments={},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is False


def test_invariant_policy_defaults_to_deny(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    assert policy.default_decision == "deny"


@pytest.mark.parametrize(
    ("tool_name", "reason"),
    [
        ("unknown_tool_xyz", "unknown_tool_denied_by_policy"),
        ("run_shell", "tool_disabled_by_policy"),
    ],
)
def test_invariant_denied_tools(
    policy_path: Path,
    tool_name: str,
    reason: str,
) -> None:
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
            tool_name=tool_name,
            arguments={"record_ids": ["1"]} if tool_name != "run_shell" else {"command": "id"},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert decision.allowed is False
    assert decision.reason == reason


def test_invariant_missing_provenance_blocks(policy_path: Path) -> None:
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
            target="tenant-a",
            provenance=None,
        ),
    )
    assert decision.reason == "missing_provenance_denied"


def test_invariant_untrusted_retrieved_cannot_authorize_external(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    decision = evaluate_policy(
        policy,
        AgentRequest(
            request_id="r",
            user_id="u",
            session_id="s",
            tenant_id="tenant-a",
            role="user",
            human_approval=True,
            user_message="x",
        ),
        ToolCallPayload(
            tool_name="send_email",
            arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.RETRIEVED,
                trust=ContextTrust.UNTRUSTED,
                context_ids=["rag"],
            ),
        ),
    )
    assert decision.allowed is False
    assert "retrieved_cannot_authorize" in decision.reason


def test_invariant_output_filter_outside_model() -> None:
    result = filter_model_output("password=secret-value-here")
    assert result.allowed is False


def test_invariant_no_real_shell_from_model_output(base_request: AgentRequest) -> None:
    result = simulate_tool_execution(
        base_request,
        ToolCallPayload(
            tool_name="run_shell",
            arguments={"command": "id"},
            target=base_request.tenant_id,
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["m"],
            ),
        ),
    )
    assert result.success is False


def test_invariant_vulnerable_path_simulation_only(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
) -> None:
    result = pipeline.run_vulnerable(base_request.model_copy(update={"scenario": "shell_attempt"}))
    assert result.tool_executed is False
    assert "would_have" in result.reason


def test_invariant_protected_path_enforces_control_plane(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
) -> None:
    result = pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    assert result.allowed is False
    assert result.path == "protected"


def test_invariant_audit_writes_for_allow_and_block(
    pipeline: ControlPlanePipeline,
    base_request: AgentRequest,
    audit_logger: AuditLogger,
) -> None:
    pipeline.run_protected(base_request.model_copy(update={"scenario": "safe_read"}))
    pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    types = {e["event_type"] for e in audit_logger.read_events()}
    assert "tool_allowed" in types
    assert "tool_blocked" in types
