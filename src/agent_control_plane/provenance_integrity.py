"""Lab-only HMAC integrity for provenance metadata (not production attestation)."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from agent_control_plane.models import Provenance

# Fake lab key for demonstrations and tests only. Do not use in production.
LAB_DEMO_HMAC_KEY = b"llm-agent-control-plane-lab-fake-hmac-key-for-tests-only"


class ProvenanceIntegrityError(ValueError):
    """Provenance failed HMAC integrity verification."""


def compute_content_hash(content: str) -> str:
    """Return lowercase hex SHA-256 of UTF-8 content (hash only; do not log raw content)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def canonicalize_provenance(provenance: Provenance) -> dict[str, Any]:
    """
    Build deterministic JSON-serializable provenance payload for signing.

    The signature field is excluded from the signed material.
    """
    return {
        "source": provenance.source.value,
        "trust": provenance.trust.value,
        "context_ids": sorted(provenance.context_ids),
        "tenant_id": provenance.tenant_id,
        "chunk_id": provenance.chunk_id,
        "content_hash": provenance.content_hash,
    }


def canonical_provenance_json(provenance: Provenance) -> str:
    """Serialize canonical provenance to stable JSON."""
    return json.dumps(canonicalize_provenance(provenance), sort_keys=True, separators=(",", ":"))


def compute_provenance_hmac(provenance: Provenance, key: bytes) -> str:
    """Return lowercase hex HMAC-SHA256 over canonical provenance JSON."""
    digest = hmac.new(key, canonical_provenance_json(provenance).encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def sign_provenance(provenance: Provenance, key: bytes) -> Provenance:
    """Return a copy of provenance with signature set from canonical HMAC."""
    signature = compute_provenance_hmac(provenance, key)
    return provenance.model_copy(update={"signature": signature})


def verify_provenance_signature(provenance: Provenance, key: bytes) -> tuple[bool, str]:
    """
    Verify HMAC signature on provenance metadata.

    Invariant: verification detects tampering only; it does not authorize tools.
    """
    if not provenance.signature:
        return False, "provenance_signature_missing"

    expected = compute_provenance_hmac(provenance, key)
    if not hmac.compare_digest(provenance.signature.lower(), expected.lower()):
        return False, "provenance_signature_invalid"

    return True, "provenance_signature_valid"


def verify_provenance_integrity(
    provenance: Provenance | None,
    key: bytes,
    *,
    require_signature: bool,
) -> tuple[bool, str]:
    """Fail closed when strict mode requires a valid signature."""
    if provenance is None:
        return False, "missing_provenance_denied"

    if not require_signature:
        return True, "provenance_signature_not_required"

    return verify_provenance_signature(provenance, key)
