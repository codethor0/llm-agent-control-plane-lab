"""Declarative provenance checks for tool authorization signals."""

from agent_control_plane.models import ContextTrust, Provenance, ProvenanceSource
from agent_control_plane.policy_types import ToolPolicy

# Sources that must never authorize tool execution (evidence only).
_SOURCES_CANNOT_AUTHORIZE: frozenset[ProvenanceSource] = frozenset(
    {
        ProvenanceSource.USER,
        ProvenanceSource.RETRIEVED,
        ProvenanceSource.TOOL_OUTPUT,
        ProvenanceSource.EXTERNAL,
        ProvenanceSource.WEB,
        ProvenanceSource.EMAIL,
        ProvenanceSource.SUPPORT_TICKET,
    }
)


def validate_provenance_for_tool(
    tool_policy: ToolPolicy,
    provenance: Provenance | None,
) -> tuple[bool, str]:
    """
    Decide whether provenance may support a tool request.

    Invariant: provenance is declarative metadata by default; optional HMAC verification
    in strict broker mode is integrity-only (see provenance_integrity.py), not authorization.
    Untrusted or user/web/email/support sources cannot authorize tools.
    Internal reviewed provenance may authorize safe internal reads only.
    """
    if provenance is None:
        return False, "missing_provenance_denied"

    if provenance.source in _SOURCES_CANNOT_AUTHORIZE:
        return False, f"{provenance.source.value}_cannot_authorize_tool_execution"

    if provenance.trust == ContextTrust.UNTRUSTED:
        return False, "untrusted_provenance_denied"

    if provenance.source == ProvenanceSource.INTERNAL_REVIEWED:
        if tool_policy.external_effect or tool_policy.destructive:
            return False, "internal_reviewed_cannot_authorize_external_or_destructive"
        return True, "internal_reviewed_provenance_allowed"

    if provenance.source in (ProvenanceSource.MODEL, ProvenanceSource.SYSTEM):
        return True, "provenance_allowed"

    return False, "provenance_source_not_permitted"
