"""Cross-cutting security invariant tests."""

from pathlib import Path

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
    ToolCallPayload,
)
from agent_control_plane.simulator import simulate_tool_execution


def test_simulator_never_executes_real_shell(base_request: AgentRequest) -> None:
    tool = ToolCallPayload(
        tool_name="run_shell",
        arguments={"command": "id"},
        target=base_request.tenant_id,
        provenance=Provenance(
            source=ProvenanceSource.MODEL,
            trust=ContextTrust.TRUSTED,
            context_ids=["m"],
        ),
    )
    result = simulate_tool_execution(base_request, tool)
    assert result.success is False
    assert "must_not_execute" in result.message


def test_free_form_model_text_not_executable(base_request: AgentRequest) -> None:
    from agent_control_plane.agent_core import run_simulated_agent

    turn = run_simulated_agent(base_request.model_copy(update={"scenario": "output_secret_leak"}))
    assert "sk-live" in turn.natural_language
    assert turn.tool_call is None


def test_missing_policy_file_denies_unknown_tools(
    tmp_path: Path,
    audit_logger: AuditLogger,
) -> None:
    from agent_control_plane.pipeline import ControlPlanePipeline

    missing = tmp_path / "missing.yaml"
    pipeline = ControlPlanePipeline(missing, audit_logger)
    request = AgentRequest(
        request_id="r",
        user_id="u",
        session_id="s",
        tenant_id="tenant-a",
        role="user",
        user_message="x",
        scenario="unknown_tool",
    )
    result = pipeline.run_protected(request)
    assert result.allowed is False
