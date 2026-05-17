"""JSON schema definitions for tool calls (structure only, not authorization)."""

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from agent_control_plane.models import ToolCallPayload


class ReadRecordsArgs(BaseModel):
    """Arguments for read_records."""

    record_ids: list[str] = Field(default_factory=list)


class SendEmailArgs(BaseModel):
    """Arguments for send_email."""

    to: str
    subject: str
    body: str


class ExportRecordsArgs(BaseModel):
    """Arguments for export_records."""

    format: str = "json"
    filter: str | None = None


class DeleteRecordsArgs(BaseModel):
    """Arguments for delete_records."""

    record_ids: list[str]


class RunShellArgs(BaseModel):
    """Arguments for run_shell (disabled by policy)."""

    command: str


_TOOL_SCHEMAS: dict[str, type[BaseModel]] = {
    "read_records": ReadRecordsArgs,
    "send_email": SendEmailArgs,
    "export_records": ExportRecordsArgs,
    "delete_records": DeleteRecordsArgs,
    "run_shell": RunShellArgs,
}


def known_tool_names() -> frozenset[str]:
    """Return tool names with registered argument schemas."""
    return frozenset(_TOOL_SCHEMAS.keys())


def validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate tool argument shape against registered schemas.

    Invariant: schema validation is not authorization. A passing result only
    means structure is well-formed; the broker and policy engine must still decide.
    """
    schema = _TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        return False, f"unknown_tool_schema:{tool_name}"
    try:
        schema.model_validate(arguments)
    except ValidationError as exc:
        return False, f"schema_validation_failed:{exc.errors()[0]['type']}"
    return True, "schema_valid"


def validate_tool_call_payload(payload: ToolCallPayload) -> tuple[bool, str]:
    """Validate a full tool call payload structure."""
    if not payload.tool_name:
        return False, "missing_tool_name"
    return validate_tool_arguments(payload.tool_name, payload.arguments)
