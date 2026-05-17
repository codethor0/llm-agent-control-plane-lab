"""Property-based tests for tool argument schema validation."""

from __future__ import annotations

from hypothesis import given
from tests.property_helpers import known_tool, unknown_tool

from agent_control_plane.models import ToolCallPayload
from agent_control_plane.schemas import (
    known_tool_names,
    validate_tool_arguments,
    validate_tool_call_payload,
)


@given(unknown_tool)
def test_property_unknown_tool_schema_rejected(tool_name: str) -> None:
    valid, reason = validate_tool_arguments(tool_name, {})
    assert valid is False
    assert reason.startswith("unknown_tool_schema:")


@given(known_tool)
def test_property_known_tool_empty_args_validates_when_schema_allows(tool_name: str) -> None:
    if tool_name == "read_records":
        args: dict[str, object] = {"record_ids": []}
    elif tool_name == "send_email":
        args = {"to": "user@example.invalid", "subject": "Lab", "body": "Fake body"}
    elif tool_name == "export_records":
        args = {"format": "json"}
    elif tool_name == "delete_records":
        args = {"record_ids": ["r-1"]}
    else:
        args = {"command": "echo lab-safe"}
    valid, reason = validate_tool_arguments(tool_name, args)
    assert valid is True
    assert reason == "schema_valid"


def test_property_missing_tool_name_rejected() -> None:
    payload = ToolCallPayload(tool_name="", arguments={})
    valid, reason = validate_tool_call_payload(payload)
    assert valid is False
    assert reason == "missing_tool_name"


@given(known_tool)
def test_property_malformed_arguments_fail_validation(tool_name: str) -> None:
    malformed: dict[str, object]
    if tool_name == "read_records":
        malformed = {"record_ids": "not-a-list"}
    elif tool_name == "send_email":
        malformed = {"to": 123, "subject": "s", "body": "b"}
    elif tool_name == "export_records":
        malformed = {"format": 99}
    elif tool_name == "delete_records":
        malformed = {"record_ids": "bad"}
    else:
        malformed = {"command": ["not", "a", "string"]}
    valid, _ = validate_tool_arguments(tool_name, malformed)
    assert valid is False


def test_property_schema_valid_does_not_imply_authorization() -> None:
    """Structure-only validation must not grant execution authority."""
    payload = ToolCallPayload(
        tool_name="send_email",
        arguments={"to": "a@b.invalid", "subject": "s", "body": "b"},
        target="tenant-a",
    )
    valid, reason = validate_tool_call_payload(payload)
    assert valid is True
    assert reason == "schema_valid"
    assert payload.tool_name in known_tool_names()
