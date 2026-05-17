"""Property-based tests for layered output filtering."""

from __future__ import annotations

import json

from hypothesis import assume, given
from hypothesis import strategies as st
from tests.property_helpers import safe_plain_text, tenant_id

from agent_control_plane.output_filter import (
    OutputDestination,
    OutputFilterContext,
    SourceSensitivity,
    filter_output,
    findings_for_audit,
)

# Lab-only token with high Shannon entropy; not a real secret.
_HIGH_ENTROPY_FAKE = "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7"


@given(safe_plain_text, tenant_id)
def test_property_safe_plain_text_allowed_on_internal(text: str, tenant: str) -> None:
    assume(len(text.strip()) > 0)
    result = filter_output(
        text,
        OutputFilterContext(tenant_id=tenant, destination=OutputDestination.INTERNAL_DISPLAY),
    )
    assert result.allowed is True


@given(tenant_id)
def test_property_high_entropy_blocked(tenant: str) -> None:
    result = filter_output(
        f"payload={_HIGH_ENTROPY_FAKE}",
        OutputFilterContext(tenant_id=tenant),
    )
    assert result.allowed is False
    assert result.reason == "high_entropy_string_blocked"


@given(tenant_id, tenant_id)
def test_property_cross_tenant_marker_blocked(tenant: str, other: str) -> None:
    assume(tenant != other)
    result = filter_output(
        f"summary tenant_id:{other}",
        OutputFilterContext(tenant_id=tenant),
    )
    assert result.allowed is False
    assert result.reason == "cross_tenant_output_blocked"


@given(safe_plain_text)
def test_property_external_destination_blocks_classification(text: str) -> None:
    payload = f"{text} classification:sensitive"
    result = filter_output(
        payload,
        OutputFilterContext(destination=OutputDestination.EXTERNAL_EMAIL),
    )
    assert result.allowed is False


@given(st.sampled_from(["status", "record_count", "debug_blob"]))
def test_property_strict_schema_unknown_key_blocked(extra_key: str) -> None:
    assume(extra_key != "status")
    ctx = OutputFilterContext(
        strict_response_schema=True,
        allowed_response_keys={"status"},
    )
    result = filter_output("", ctx, structured_output={"status": "ok", extra_key: "x"})
    assert result.allowed is False
    assert result.reason == "unknown_response_key_blocked"


def test_property_sensitive_key_always_blocked() -> None:
    ctx = OutputFilterContext(
        strict_response_schema=True,
        allowed_response_keys={"status", "password"},
    )
    result = filter_output("", ctx, structured_output={"status": "ok", "password": "lab-fake"})
    assert result.allowed is False
    assert result.reason == "sensitive_response_key_blocked"


def test_property_audit_findings_redacted_only() -> None:
    result = filter_output(
        "password=lab-fake-property-test",
        OutputFilterContext(),
    )
    assert not result.allowed
    serialized = json.dumps(findings_for_audit(result.findings))
    assert "lab-fake" not in serialized or "REDACTED" in serialized
    assert all("redacted_sample" in item for item in findings_for_audit(result.findings))


def test_property_sensitive_source_blocks_external() -> None:
    ctx = OutputFilterContext(
        destination=OutputDestination.WEBHOOK,
        source_sensitivity=SourceSensitivity.RESTRICTED,
    )
    result = filter_output("benign summary text", ctx)
    assert result.allowed is False
    assert result.reason == "sensitive_source_external_destination_blocked"
