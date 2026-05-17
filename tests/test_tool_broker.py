"""Tool broker authority boundary tests."""

from pathlib import Path

from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.policy_engine import load_policy
from agent_control_plane.tool_broker import broker_tool_request


def test_broker_denies_unknown_tool(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    request = AgentRequest(
        request_id="r",
        user_id="u",
        session_id="s",
        tenant_id="tenant-a",
        role="user",
        user_message="x",
    )
    tool = ToolCallPayload(
        tool_name="deploy_malware",
        arguments={},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    decision = broker_tool_request(request, policy, tool)
    assert decision.allowed is False
    assert decision.schema_valid is False


def test_broker_denies_valid_schema_when_policy_denies(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    request = AgentRequest(
        request_id="r",
        user_id="u",
        session_id="s",
        tenant_id="tenant-a",
        role="user",
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
