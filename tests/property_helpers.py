"""Shared Hypothesis strategies for property-based security tests."""

from __future__ import annotations

from hypothesis import strategies as st

from agent_control_plane.models import ContextTrust, ProvenanceSource
from agent_control_plane.schemas import known_tool_names

KNOWN_TOOLS = sorted(known_tool_names())
TENANT_IDS = ("tenant-a", "tenant-b", "tenant-c")
ROLES = ("user", "admin", "guest")
NON_AUTHORIZING_SOURCES = (
    ProvenanceSource.USER,
    ProvenanceSource.RETRIEVED,
    ProvenanceSource.TOOL_OUTPUT,
    ProvenanceSource.WEB,
    ProvenanceSource.EMAIL,
    ProvenanceSource.SUPPORT_TICKET,
    ProvenanceSource.EXTERNAL,
)

safe_identifier = st.from_regex(r"[a-z][a-z0-9_-]{0,15}", fullmatch=True)
tenant_id = st.sampled_from(TENANT_IDS)
role = st.sampled_from(ROLES)
known_tool = st.sampled_from(KNOWN_TOOLS)
unknown_tool = st.from_regex(r"[a-z][a-z0-9_-]{0,12}", fullmatch=True).filter(
    lambda name: name not in KNOWN_TOOLS
)
context_ids = st.lists(safe_identifier, min_size=0, max_size=4, unique=True)

safe_plain_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
        min_codepoint=32,
        max_codepoint=126,
    ),
    min_size=0,
    max_size=64,
).filter(
    lambda value: (
        "sk-live" not in value
        and "BEGIN PRIVATE KEY" not in value
        and "eyJ" not in value
        and "password=" not in value.lower()
        and "api_key=" not in value.lower()
        and "tenant_id:" not in value.lower()
    )
)

provenance_source = st.sampled_from(list(ProvenanceSource))
non_authorizing_source = st.sampled_from(NON_AUTHORIZING_SOURCES)
context_trust = st.sampled_from(list(ContextTrust))
