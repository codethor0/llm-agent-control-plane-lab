"""Safe simulated tool execution (no real external effects)."""

from typing import Any

from agent_control_plane.models import AgentRequest, SimulationResult, ToolCallPayload


def simulate_tool_execution(
    request: AgentRequest,
    tool_call: ToolCallPayload,
) -> SimulationResult:
    """
    Simulate tool execution locally without shell, network, or credentials.

    Invariant: no real external tools execute; output is clearly synthetic.
    """
    tool = tool_call.tool_name
    tenant = request.tenant_id

    if tool == "read_records":
        ids = tool_call.arguments.get("record_ids", [])
        return SimulationResult(
            success=True,
            message="simulated_read_records",
            simulated_output={
                "tenant_id": tenant,
                "records": [{"id": rid, "value": "simulated"} for rid in ids],
            },
        )

    if tool == "send_email":
        return SimulationResult(
            success=True,
            message="simulated_send_email",
            simulated_output={
                "to": tool_call.arguments.get("to"),
                "status": "simulated_queued",
                "note": "no real email sent",
            },
        )

    if tool == "export_records":
        return SimulationResult(
            success=True,
            message="simulated_export_records",
            simulated_output={
                "format": tool_call.arguments.get("format", "json"),
                "rows": 3,
                "note": "simulated export only",
            },
        )

    if tool == "delete_records":
        return SimulationResult(
            success=True,
            message="simulated_delete_records",
            simulated_output={
                "deleted_ids": tool_call.arguments.get("record_ids", []),
                "note": "simulated delete only",
            },
        )

    if tool == "run_shell":
        return SimulationResult(
            success=False,
            message="run_shell_must_not_execute",
            simulated_output={"note": "policy should block before simulation"},
        )

    return SimulationResult(
        success=False,
        message=f"unknown_tool_not_simulated:{tool}",
        simulated_output={},
    )


def simulate_vulnerable_execution(tool_call: ToolCallPayload) -> dict[str, Any]:
    """
    Simulate what an unprotected agent might do (lab demonstration only).

    Invariant: still no real shell or network; returns a labeled unsafe decision record.
    """
    if tool_call.tool_name == "run_shell":
        command = str(tool_call.arguments.get("command", ""))
        return {
            "unsafe_decision": "would_have_invoked_shell",
            "simulated_command": command,
            "actually_executed": False,
            "warning": "vulnerable_path_simulation_only",
        }
    if tool_call.tool_name == "send_email":
        return {
            "unsafe_decision": "would_have_sent_email_without_broker",
            "actually_executed": False,
            "warning": "vulnerable_path_simulation_only",
        }
    return {
        "unsafe_decision": f"would_have_called_{tool_call.tool_name}",
        "actually_executed": False,
        "warning": "vulnerable_path_simulation_only",
    }
