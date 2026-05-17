"""Lab HMAC provenance integrity tests (not production attestation)."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

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
from agent_control_plane.provenance import validate_provenance_for_tool
from agent_control_plane.provenance_integrity import (
    LAB_DEMO_HMAC_KEY,
    canonical_provenance_json,
    compute_content_hash,
    compute_provenance_hmac,
    sign_provenance,
    verify_provenance_integrity,
    verify_provenance_signature,
)
from agent_control_plane.tool_broker import broker_tool_request

SAMPLE_CONTENT = "harmless sample text for lab provenance hash"


def _base_provenance(**kwargs: object) -> Provenance:
    base: dict[str, object] = {
        "source": ProvenanceSource.MODEL,
        "trust": ContextTrust.TRUSTED,
        "context_ids": ["ctx-1"],
        "tenant_id": "tenant-a",
        "chunk_id": "chunk-1",
        "content_hash": compute_content_hash(SAMPLE_CONTENT),
    }
    base.update(kwargs)
    return Provenance.model_validate(base)


def _request(**kwargs: object) -> AgentRequest:
    base: dict[str, object] = {
        "request_id": "req-prov",
        "user_id": "user-1",
        "session_id": "sess-1",
        "tenant_id": "tenant-a",
        "role": "user",
        "human_approval": False,
        "user_message": "Read records.",
    }
    base.update(kwargs)
    return AgentRequest.model_validate(base)


def test_canonical_provenance_signature_is_deterministic() -> None:
    provenance = _base_provenance()
    first = compute_provenance_hmac(provenance, LAB_DEMO_HMAC_KEY)
    second = compute_provenance_hmac(provenance, LAB_DEMO_HMAC_KEY)
    assert first == second
    assert canonical_provenance_json(provenance) == canonical_provenance_json(provenance)


def test_valid_signed_provenance_verifies() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    ok, reason = verify_provenance_signature(signed, LAB_DEMO_HMAC_KEY)
    assert ok is True
    assert reason == "provenance_signature_valid"


def test_modified_tenant_id_fails_verification() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    tampered = signed.model_copy(update={"tenant_id": "tenant-b"})
    ok, reason = verify_provenance_signature(tampered, LAB_DEMO_HMAC_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


def test_modified_trust_level_fails_verification() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    tampered = signed.model_copy(update={"trust": ContextTrust.UNTRUSTED})
    ok, reason = verify_provenance_signature(tampered, LAB_DEMO_HMAC_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


def test_modified_source_fails_verification() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    tampered = signed.model_copy(update={"source": ProvenanceSource.INTERNAL_REVIEWED})
    ok, reason = verify_provenance_signature(tampered, LAB_DEMO_HMAC_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


def test_modified_content_hash_fails_verification() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    tampered = signed.model_copy(
        update={"content_hash": compute_content_hash("different harmless text")}
    )
    ok, reason = verify_provenance_signature(tampered, LAB_DEMO_HMAC_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


def test_missing_signature_fails_in_strict_mode() -> None:
    unsigned = _base_provenance()
    ok, reason = verify_provenance_integrity(
        unsigned,
        LAB_DEMO_HMAC_KEY,
        require_signature=True,
    )
    assert ok is False
    assert reason == "provenance_signature_missing"


def test_invalid_signature_fails_in_strict_mode() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    invalid = signed.model_copy(update={"signature": "0" * 64})
    ok, reason = verify_provenance_signature(invalid, LAB_DEMO_HMAC_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


def test_valid_signature_does_not_bypass_broker_policy(policy_path: Path) -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    decision = broker_tool_request(
        _request(),
        load_policy(policy_path),
        ToolCallPayload(
            tool_name="unknown_tool_xyz",
            arguments={},
            target="tenant-a",
            provenance=signed,
        ),
        require_provenance_signature=True,
    )
    assert decision.allowed is False
    assert "unknown_tool" in decision.reason


def test_signed_user_generated_cannot_authorize_external_effects() -> None:
    signed = sign_provenance(
        Provenance(
            source=ProvenanceSource.USER,
            trust=ContextTrust.TRUSTED,
            context_ids=["u1"],
            tenant_id="tenant-a",
        ),
        LAB_DEMO_HMAC_KEY,
    )
    ok, reason = validate_provenance_for_tool(
        ToolPolicy.model_validate(
            {
                "enabled": True,
                "risk_level": "high",
                "external_effect": True,
                "destructive": False,
                "requires_human_approval": True,
                "allowed_roles": ["user"],
            }
        ),
        signed,
    )
    assert ok is False
    assert reason == "user_cannot_authorize_tool_execution"


def test_signed_internal_reviewed_allows_safe_internal_read() -> None:
    signed = sign_provenance(
        Provenance(
            source=ProvenanceSource.INTERNAL_REVIEWED,
            trust=ContextTrust.TRUSTED,
            context_ids=["review-1"],
            tenant_id="tenant-a",
            chunk_id="chunk-review",
            content_hash=compute_content_hash(SAMPLE_CONTENT),
        ),
        LAB_DEMO_HMAC_KEY,
    )
    ok, reason = validate_provenance_for_tool(
        ToolPolicy.model_validate(
            {
                "enabled": True,
                "risk_level": "low",
                "external_effect": False,
                "destructive": False,
                "requires_human_approval": False,
                "allowed_roles": ["user"],
            }
        ),
        signed,
    )
    assert ok is True
    assert reason == "internal_reviewed_provenance_allowed"


def test_signing_key_not_in_audit_log(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    audit_logger = AuditLogger(tmp_path / "audit.jsonl")
    pipeline = ControlPlanePipeline(
        policy_path,
        audit_logger,
        require_provenance_signature=True,
    )
    pipeline.run_protected(base_request.model_copy(update={"scenario": "strict_signed_read"}))
    serialized = tmp_path.joinpath("audit.jsonl").read_text(encoding="utf-8")
    assert LAB_DEMO_HMAC_KEY.decode("utf-8") not in serialized


def test_compare_digest_used_for_signature_verification() -> None:
    signed = sign_provenance(_base_provenance(), LAB_DEMO_HMAC_KEY)
    with mock.patch("agent_control_plane.provenance_integrity.hmac.compare_digest") as compare:
        compare.return_value = True
        ok, _ = verify_provenance_signature(signed, LAB_DEMO_HMAC_KEY)
        assert ok is True
        compare.assert_called_once()


def test_strict_protected_pipeline_blocks_unsigned_provenance(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit.jsonl"),
        require_provenance_signature=True,
    )
    result = pipeline.run_protected(base_request.model_copy(update={"scenario": "safe_read"}))
    assert result.allowed is False
    assert result.stage == "tool_broker"
    assert result.reason == "provenance_signature_missing"


def test_strict_protected_pipeline_blocks_tampered_provenance(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    audit_logger = AuditLogger(tmp_path / "audit.jsonl")
    pipeline = ControlPlanePipeline(
        policy_path,
        audit_logger,
        require_provenance_signature=True,
    )
    signed_request = base_request.model_copy(update={"scenario": "strict_signed_read"})
    result = pipeline.run_protected(signed_request)
    assert result.allowed is True

    tampered_pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit-tampered.jsonl"),
        require_provenance_signature=True,
    )

    class _TamperedAgentCore:
        @staticmethod
        def run(request: AgentRequest):  # type: ignore[no-untyped-def]
            from agent_control_plane.agent_core import run_simulated_agent

            turn = run_simulated_agent(
                request.model_copy(update={"scenario": "strict_signed_read"})
            )
            assert turn.tool_call is not None
            assert turn.tool_call.provenance is not None
            turn.tool_call.provenance = turn.tool_call.provenance.model_copy(
                update={"tenant_id": "tenant-b"}
            )
            return turn

    with mock.patch(
        "agent_control_plane.pipeline.run_simulated_agent",
        side_effect=_TamperedAgentCore.run,
    ):
        blocked = tampered_pipeline.run_protected(
            base_request.model_copy(update={"scenario": "strict_signed_read"})
        )
    assert blocked.allowed is False
    assert blocked.reason == "provenance_signature_invalid"


def test_strict_mode_allows_valid_signed_safe_read(
    policy_path: Path,
    base_request: AgentRequest,
    tmp_path: Path,
) -> None:
    pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit-signed.jsonl"),
        require_provenance_signature=True,
    )
    result = pipeline.run_protected(
        base_request.model_copy(update={"scenario": "strict_signed_read"})
    )
    assert result.allowed is True
    assert result.stage == "simulation"


def test_unsigned_provenance_skips_hmac_when_not_strict(policy_path: Path) -> None:
    decision = broker_tool_request(
        _request(),
        load_policy(policy_path),
        ToolCallPayload(
            tool_name="read_records",
            arguments={"record_ids": ["1"]},
            target="tenant-a",
            provenance=Provenance(
                source=ProvenanceSource.MODEL,
                trust=ContextTrust.TRUSTED,
                context_ids=["model-turn"],
            ),
        ),
        require_provenance_signature=False,
    )
    assert decision.allowed is True
