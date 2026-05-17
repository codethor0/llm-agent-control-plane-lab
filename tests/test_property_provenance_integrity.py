"""Property-based tests for lab HMAC provenance integrity."""

from __future__ import annotations

from hypothesis import assume, given
from tests.property_helpers import context_ids, safe_identifier, tenant_id

from agent_control_plane.models import ContextTrust, Provenance, ProvenanceSource
from agent_control_plane.policy_types import ToolPolicy
from agent_control_plane.provenance import validate_provenance_for_tool
from agent_control_plane.provenance_integrity import (
    LAB_DEMO_HMAC_KEY,
    compute_provenance_hmac,
    sign_provenance,
    verify_provenance_integrity,
    verify_provenance_signature,
)

_FAKE_KEY = LAB_DEMO_HMAC_KEY


def _base_provenance(tenant: str, ctx: list[str]) -> Provenance:
    return Provenance(
        source=ProvenanceSource.MODEL,
        trust=ContextTrust.TRUSTED,
        context_ids=ctx,
        tenant_id=tenant,
        chunk_id="chunk-prop",
        content_hash="abc123" * 8,
    )


@given(tenant_id, context_ids)
def test_property_signed_provenance_verifies(tenant: str, ctx: list[str]) -> None:
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    ok, reason = verify_provenance_signature(signed, _FAKE_KEY)
    assert ok is True
    assert reason == "provenance_signature_valid"


@given(tenant_id, context_ids, safe_identifier)
def test_property_tampered_signature_fails(tenant: str, ctx: list[str], suffix: str) -> None:
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    tampered = signed.model_copy(update={"signature": (signed.signature or "") + suffix[:4]})
    ok, reason = verify_provenance_signature(tampered, _FAKE_KEY)
    assert ok is False
    assert reason == "provenance_signature_invalid"


@given(tenant_id, context_ids, tenant_id)
def test_property_tenant_mutation_breaks_signature(
    tenant: str,
    ctx: list[str],
    other_tenant: str,
) -> None:
    assume(tenant != other_tenant)
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    tampered = signed.model_copy(update={"tenant_id": other_tenant})
    ok, _ = verify_provenance_signature(tampered, _FAKE_KEY)
    assert ok is False


@given(tenant_id, context_ids)
def test_property_trust_mutation_breaks_signature(tenant: str, ctx: list[str]) -> None:
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    tampered = signed.model_copy(update={"trust": ContextTrust.UNTRUSTED})
    ok, _ = verify_provenance_signature(tampered, _FAKE_KEY)
    assert ok is False


@given(tenant_id, context_ids, safe_identifier)
def test_property_content_hash_mutation_breaks_signature(
    tenant: str,
    ctx: list[str],
    extra: str,
) -> None:
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    tampered = signed.model_copy(update={"content_hash": (signed.content_hash or "") + extra})
    ok, _ = verify_provenance_signature(tampered, _FAKE_KEY)
    assert ok is False


@given(tenant_id, context_ids)
def test_property_source_mutation_breaks_signature(tenant: str, ctx: list[str]) -> None:
    signed = sign_provenance(_base_provenance(tenant, ctx), _FAKE_KEY)
    tampered = signed.model_copy(update={"source": ProvenanceSource.RETRIEVED})
    ok, _ = verify_provenance_signature(tampered, _FAKE_KEY)
    assert ok is False


@given(tenant_id, context_ids)
def test_property_hmac_is_deterministic(tenant: str, ctx: list[str]) -> None:
    prov = _base_provenance(tenant, ctx)
    assert compute_provenance_hmac(prov, _FAKE_KEY) == compute_provenance_hmac(prov, _FAKE_KEY)


def test_property_signature_verification_not_authorization() -> None:
    """Valid HMAC does not authorize tools from non-authorizing sources."""
    signed = sign_provenance(
        Provenance(
            source=ProvenanceSource.RETRIEVED,
            trust=ContextTrust.UNTRUSTED,
            context_ids=["rag-1"],
        ),
        _FAKE_KEY,
    )
    ok, _ = verify_provenance_signature(signed, _FAKE_KEY)
    assert ok is True
    tool_policy = ToolPolicy.model_validate(
        {
            "enabled": True,
            "risk_level": "high",
            "external_effect": True,
            "destructive": False,
            "requires_human_approval": True,
            "allowed_roles": ["user"],
        }
    )
    allowed, reason = validate_provenance_for_tool(tool_policy, signed)
    assert allowed is False
    assert "cannot_authorize" in reason


@given(tenant_id, context_ids)
def test_property_strict_mode_requires_signature(tenant: str, ctx: list[str]) -> None:
    unsigned = _base_provenance(tenant, ctx)
    ok, reason = verify_provenance_integrity(unsigned, _FAKE_KEY, require_signature=True)
    assert ok is False
    assert reason == "provenance_signature_missing"
