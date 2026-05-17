"""Schema validation is structure only, not authorization."""

from agent_control_plane.models import ContextTrust, Provenance, ProvenanceSource, ToolCallPayload
from agent_control_plane.schemas import validate_tool_arguments, validate_tool_call_payload


def test_valid_read_records_schema_passes() -> None:
    ok, reason = validate_tool_arguments("read_records", {"record_ids": ["r-1"]})
    assert ok is True
    assert reason == "schema_valid"


def test_invalid_send_email_schema_fails() -> None:
    ok, reason = validate_tool_arguments("send_email", {"to": "a@b.invalid"})
    assert ok is False
    assert reason.startswith("schema_validation_failed:")


def test_unknown_tool_schema_fails() -> None:
    ok, reason = validate_tool_arguments("deploy_malware", {})
    assert ok is False
    assert "unknown_tool_schema" in reason


def test_schema_valid_does_not_imply_authorization() -> None:
    """Well-formed malicious tool call still only passes structure check."""
    payload = ToolCallPayload(
        tool_name="send_email",
        arguments={
            "to": "x@example.invalid",
            "subject": "hi",
            "body": "data",
        },
        provenance=Provenance(
            source=ProvenanceSource.RETRIEVED,
            trust=ContextTrust.UNTRUSTED,
            context_ids=["inj"],
        ),
    )
    ok, _ = validate_tool_call_payload(payload)
    assert ok is True
