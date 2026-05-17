"""Lab approval token binding, replay protection, and broker integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agent_control_plane.approval_tokens import (
    clear_used_approval_tokens,
    compute_action_fingerprint,
    create_approval_token,
    mark_approval_token_used,
    verify_approval_token,
)
from agent_control_plane.audit_logger import AuditLogger
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
from agent_control_plane.provenance_integrity import LAB_DEMO_HMAC_KEY, sign_provenance
from agent_control_plane.tool_broker import broker_tool_request

FAKE_SECRET_IN_REASON = "sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789"


@pytest.fixture(autouse=True)
def _reset_used_approval_tokens() -> None:
    clear_used_approval_tokens()


def _request(**kwargs: object) -> AgentRequest:
    base: dict[str, object] = {
        "request_id": "req-apr",
        "user_id": "user-1",
        "session_id": "sess-1",
        "tenant_id": "tenant-a",
        "role": "user",
        "human_approval": False,
        "user_message": "Send notice.",
    }
    base.update(kwargs)
    return AgentRequest.model_validate(base)


def _email_tool(**kwargs: object) -> ToolCallPayload:
    base: dict[str, object] = {
        "tool_name": "send_email",
        "arguments": {"to": "user@example.invalid", "subject": "Notice", "body": "Hello"},
        "target": "tenant-a",
        "provenance": Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["model-turn"],
        ),
    }
    base.update(kwargs)
    return ToolCallPayload.model_validate(base)


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


def test_approval_token_fingerprint_is_deterministic(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    first = compute_action_fingerprint(request, tool, tool_policy.risk_level.value)
    second = compute_action_fingerprint(request, tool, tool_policy.risk_level.value)
    assert first == second


def test_valid_approval_token_verifies_for_matching_request(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    ok, reason = verify_approval_token(token, request, tool, tool_policy.risk_level.value)
    assert ok is True
    assert reason == "approval_token_valid"


def test_missing_approval_token_blocks_when_required(policy_path: Path) -> None:
    decision = broker_tool_request(
        _request(),
        load_policy(policy_path),
        _email_tool(),
        require_approval_token=True,
    )
    assert decision.allowed is False
    assert decision.reason == "approval_token_missing"


def test_expired_approval_token_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    expired_at = datetime.now(UTC) - timedelta(seconds=60)
    token = create_approval_token(
        "approver-1",
        request,
        tool,
        tool_policy,
        approved_at=expired_at,
        ttl_seconds=1,
    )
    ok, reason = verify_approval_token(
        token,
        request,
        tool,
        tool_policy.risk_level.value,
        now=datetime.now(UTC),
    )
    assert ok is False
    assert reason == "approval_token_expired"


def test_used_approval_token_blocks_replay(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    mark_approval_token_used(token.approval_id)
    ok, reason = verify_approval_token(token, request, tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_reused"


def test_wrong_tool_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_tool = tool.model_copy(update={"tool_name": "export_records"})
    ok, reason = verify_approval_token(token, request, wrong_tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_tool_mismatch"


def test_wrong_target_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_tool = tool.model_copy(update={"target": "tenant-b"})
    ok, reason = verify_approval_token(token, request, wrong_tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_target_mismatch"


def test_wrong_tenant_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_request = request.model_copy(update={"tenant_id": "tenant-b"})
    ok, reason = verify_approval_token(token, wrong_request, tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_tenant_mismatch"


def test_wrong_user_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_request = request.model_copy(update={"user_id": "user-2"})
    ok, reason = verify_approval_token(token, wrong_request, tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_user_mismatch"


def test_changed_source_context_ids_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_tool = tool.model_copy(
        update={
            "provenance": Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["other-context"],
            )
        }
    )
    ok, reason = verify_approval_token(token, request, wrong_tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_context_mismatch"


def test_changed_risk_level_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    ok, reason = verify_approval_token(token, request, tool, "low")
    assert ok is False
    assert reason == "approval_token_risk_mismatch"


def test_changed_provenance_fingerprint_blocks(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool()
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_tool = tool.model_copy(
        update={
            "provenance": Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["model-turn"],
                tenant_id="tenant-a",
                chunk_id="chunk-2",
            )
        }
    )
    ok, reason = verify_approval_token(token, request, wrong_tool, tool_policy.risk_level.value)
    assert ok is False
    assert reason == "approval_token_provenance_mismatch"


def test_approval_token_does_not_bypass_policy_deny(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool(tool_name="unknown_tool_xyz", arguments={})
    token = create_approval_token("approver-1", request, tool, tool_policy)
    decision = broker_tool_request(
        request.model_copy(update={"approval_token": token}),
        policy,
        tool,
    )
    assert decision.allowed is False
    assert "unknown_tool" in decision.reason


def test_approval_token_does_not_enable_run_shell(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["run_shell"]
    request = _request(role="admin")
    tool = ToolCallPayload(
        tool_name="run_shell",
        arguments={"command": "echo simulated"},
        target="tenant-a",
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["model-turn"],
        ),
    )
    token = create_approval_token("approver-1", request, tool, tool_policy)
    decision = broker_tool_request(
        request.model_copy(update={"approval_token": token, "human_approval": True}),
        policy,
        tool,
    )
    assert decision.allowed is False
    assert decision.reason == "tool_disabled_by_policy"


def test_approval_token_does_not_bypass_invalid_provenance_signature_in_strict_mode(
    policy_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    provenance = sign_provenance(
        Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["model-turn"],
            tenant_id="tenant-a",
        ),
        LAB_DEMO_HMAC_KEY,
    )
    tool = _email_tool(provenance=provenance)
    token = create_approval_token("approver-1", request, tool, tool_policy)
    tampered_tool = tool.model_copy(
        update={"provenance": provenance.model_copy(update={"tenant_id": "tenant-b"})}
    )
    decision = broker_tool_request(
        request.model_copy(update={"approval_token": token}),
        policy,
        tampered_tool,
        require_provenance_signature=True,
    )
    assert decision.allowed is False
    assert decision.reason == "provenance_signature_invalid"


def test_token_marked_used_after_successful_pipeline_execution(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    tool = _email_tool()
    token = create_approval_token("approver-1", base_request, tool, tool_policy)
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(
        base_request.model_copy(
            update={
                "scenario": "send_email_approved",
                "approval_token": token,
            }
        )
    )
    assert result.allowed is True
    replay = verify_approval_token(token, base_request, tool, tool_policy.risk_level.value)
    assert replay[0] is False
    assert replay[1] == "approval_token_reused"


def test_audit_event_contains_approval_metadata_not_secrets(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    tool = _email_tool()
    token = create_approval_token(
        "approver-1",
        base_request,
        tool,
        tool_policy,
        approval_reason=FAKE_SECRET_IN_REASON,
    )
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "approval_token": token})
    )
    log_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert token.approval_id in log_text
    assert token.approver_id in log_text
    assert "approval_decision" in log_text
    assert LAB_DEMO_HMAC_KEY.decode("utf-8") not in log_text
    assert FAKE_SECRET_IN_REASON not in log_text


def test_approved_send_email_with_valid_token_pipeline(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool = _email_tool()
    token = create_approval_token("approver-1", base_request, tool, policy.tools["send_email"])
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "approval_token": token})
    )
    assert result.allowed is True
    assert result.stage == "simulation"


def test_send_email_with_expired_token_blocked(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool = _email_tool()
    token = create_approval_token(
        "approver-1",
        base_request,
        tool,
        policy.tools["send_email"],
        approved_at=datetime.now(UTC) - timedelta(hours=2),
        ttl_seconds=1,
    )
    pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit.jsonl"),
        require_approval_token=True,
    )
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "approval_token": token})
    )
    assert result.allowed is False
    assert result.reason == "approval_token_expired"


def test_send_email_with_replayed_token_blocked(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    policy = load_policy(policy_path)
    tool = _email_tool()
    token = create_approval_token("approver-1", base_request, tool, policy.tools["send_email"])
    mark_approval_token_used(token.approval_id)
    pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit.jsonl"),
        require_approval_token=True,
    )
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "send_email_approved", "approval_token": token})
    )
    assert result.allowed is False
    assert result.reason == "approval_token_reused"


def test_approval_token_for_wrong_target_blocked(policy_path: Path) -> None:
    policy = load_policy(policy_path)
    tool_policy = policy.tools["send_email"]
    request = _request()
    tool = _email_tool(target="tenant-a")
    token = create_approval_token("approver-1", request, tool, tool_policy)
    wrong_tool = tool.model_copy(update={"target": "tenant-b"})
    decision = broker_tool_request(
        request.model_copy(update={"approval_token": token}),
        policy,
        wrong_tool,
        require_approval_token=True,
    )
    assert decision.allowed is False
    assert decision.reason in {
        "approval_token_target_mismatch",
        "cross_tenant_target_denied",
    }
