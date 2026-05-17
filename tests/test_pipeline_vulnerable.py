"""Vulnerable path is simulation-only and does not enforce broker."""

from agent_control_plane.models import AgentRequest


def test_vulnerable_path_simulates_unsafe_shell_decision(
    pipeline: object,
    base_request: AgentRequest,
) -> None:
    from agent_control_plane.pipeline import ControlPlanePipeline

    assert isinstance(pipeline, ControlPlanePipeline)
    result = pipeline.run_vulnerable(base_request.model_copy(update={"scenario": "shell_attempt"}))
    assert result.path == "vulnerable"
    assert result.allowed is True
    assert "would_have_invoked_shell" in result.reason
    assert result.tool_executed is False


def test_protected_path_blocks_same_shell_scenario(
    pipeline: object,
    base_request: AgentRequest,
) -> None:
    from agent_control_plane.pipeline import ControlPlanePipeline

    assert isinstance(pipeline, ControlPlanePipeline)
    result = pipeline.run_protected(base_request.model_copy(update={"scenario": "shell_attempt"}))
    assert result.allowed is False
