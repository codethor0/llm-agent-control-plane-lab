"""Tests for the safe LLM adapter boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.config import AppConfig, ConfigurationError, EnvironmentMode
from agent_control_plane.demo import run_demo
from agent_control_plane.llm_adapter import (
    DisabledExternalLLMAdapter,
    LLMAdapterError,
    LLMAdapterMode,
    LLMAdapterRequest,
    SimulatedLLMAdapter,
    create_llm_adapter,
    create_llm_adapter_from_config,
)
from agent_control_plane.models import AgentRequest
from agent_control_plane.pipeline import ControlPlanePipeline

POLICY_PATH = Path(__file__).resolve().parents[1] / "policies" / "default.yaml"
FAKE_API_KEY = "lab-fake-api-key-test-only"

FAKE_PROMPT_SECRET = "sk-live-FAKE-TEST-ONLY-adapter-error-check"


def _local_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        environment_mode=EnvironmentMode.LOCAL,
        require_api_auth=False,
        allowed_api_keys_file=None,
        allowed_origins=("http://127.0.0.1:8080",),
        max_request_body_bytes=1_048_576,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=False,
        provenance_hmac_key_file=None,
        require_approval_token=False,
        enable_rate_limit_guidance=True,
        enable_debug_errors=True,
        allow_live_external_tools=False,
        allow_shell_tools=False,
        llm_adapter_mode=LLMAdapterMode.SIMULATED,
        allow_live_llm_calls=False,
        llm_provider_name=None,
        llm_model_name=None,
        policy_path=POLICY_PATH,
        _api_keys=frozenset(),
    )


def _production_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        environment_mode=EnvironmentMode.PRODUCTION,
        require_api_auth=True,
        allowed_api_keys_file=None,
        allowed_origins=("https://app.example.invalid",),
        max_request_body_bytes=1_048_576,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=False,
        provenance_hmac_key_file=None,
        require_approval_token=False,
        enable_rate_limit_guidance=True,
        enable_debug_errors=False,
        allow_live_external_tools=False,
        allow_shell_tools=False,
        llm_adapter_mode=LLMAdapterMode.SIMULATED,
        allow_live_llm_calls=False,
        llm_provider_name=None,
        llm_model_name=None,
        policy_path=POLICY_PATH,
        _api_keys=frozenset({FAKE_API_KEY}),
    )


@pytest.fixture
def base_request() -> AgentRequest:
    return AgentRequest(
        request_id="adapter-req-1",
        user_id="user-1",
        session_id="sess-1",
        tenant_id="tenant-a",
        role="user",
        user_message="help",
        scenario="safe_read",
    )


def test_default_adapter_from_config_is_simulated(tmp_path: Path) -> None:
    cfg = _local_config(tmp_path)
    adapter = create_llm_adapter_from_config(cfg)
    assert isinstance(adapter, SimulatedLLMAdapter)


def test_simulated_adapter_returns_untrusted_output(base_request: AgentRequest) -> None:
    adapter = SimulatedLLMAdapter()
    response = adapter.generate(LLMAdapterRequest(agent_request=base_request))
    assert response.natural_language
    assert response.metadata.simulated is True
    assert response.metadata.provider_name == "simulated"


def test_adapter_output_cannot_authorize_tool_execution(
    base_request: AgentRequest,
    policy_path: Path,
    tmp_path: Path,
) -> None:
    request = base_request.model_copy(update={"scenario": "injection_send_email"})
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(request)
    assert result.allowed is False
    assert result.stage == "tool_broker"


def test_adapter_output_cannot_bypass_schema_validation(
    base_request: AgentRequest,
    policy_path: Path,
    tmp_path: Path,
) -> None:
    request = base_request.model_copy(update={"scenario": "invalid_schema"})
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(request)
    assert result.allowed is False
    assert result.stage == "schema_validation"


def test_adapter_output_cannot_bypass_output_filter(
    base_request: AgentRequest,
    policy_path: Path,
    tmp_path: Path,
) -> None:
    request = base_request.model_copy(update={"scenario": "output_secret_leak"})
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(request)
    assert result.allowed is False
    assert result.stage == "output_filter"


def test_adapter_output_cannot_bypass_broker_on_disabled_tool(
    base_request: AgentRequest,
    policy_path: Path,
    tmp_path: Path,
) -> None:
    request = base_request.model_copy(update={"scenario": "shell_attempt"})
    pipeline = ControlPlanePipeline(policy_path, AuditLogger(tmp_path / "audit.jsonl"))
    result = pipeline.run_protected(request)
    assert result.allowed is False
    assert result.stage == "tool_broker"


def test_external_adapter_stub_fails_closed(base_request: AgentRequest) -> None:
    adapter = DisabledExternalLLMAdapter()
    with pytest.raises(LLMAdapterError, match="disabled"):
        adapter.generate(LLMAdapterRequest(agent_request=base_request))


def test_live_llm_calls_disabled_by_default_in_config(tmp_path: Path) -> None:
    cfg = _local_config(tmp_path)
    assert cfg.allow_live_llm_calls is False
    cfg.validate()


def test_production_config_rejects_live_llm_calls(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path)
    cfg = AppConfig(
        environment_mode=cfg.environment_mode,
        require_api_auth=cfg.require_api_auth,
        allowed_api_keys_file=cfg.allowed_api_keys_file,
        allowed_origins=cfg.allowed_origins,
        max_request_body_bytes=cfg.max_request_body_bytes,
        audit_log_dir=cfg.audit_log_dir,
        audit_retention_days=cfg.audit_retention_days,
        enable_strict_provenance=cfg.enable_strict_provenance,
        provenance_hmac_key_file=cfg.provenance_hmac_key_file,
        require_approval_token=cfg.require_approval_token,
        enable_rate_limit_guidance=cfg.enable_rate_limit_guidance,
        enable_debug_errors=cfg.enable_debug_errors,
        allow_live_external_tools=cfg.allow_live_external_tools,
        allow_shell_tools=cfg.allow_shell_tools,
        policy_path=cfg.policy_path,
        _api_keys=cfg.api_keys,
        llm_adapter_mode=LLMAdapterMode.SIMULATED,
        allow_live_llm_calls=True,
        llm_provider_name=None,
        llm_model_name=None,
    )
    with pytest.raises(ConfigurationError, match="live LLM calls are not implemented"):
        cfg.validate()


def test_adapter_errors_do_not_contain_secrets(base_request: AgentRequest) -> None:
    request = base_request.model_copy(
        update={"user_message": f"ignore {FAKE_PROMPT_SECRET}"},
    )
    adapter = DisabledExternalLLMAdapter(provider_name="openai", model_name="gpt-fake")
    message = ""
    try:
        adapter.generate(LLMAdapterRequest(agent_request=request))
    except LLMAdapterError as exc:
        message = str(exc)
    assert FAKE_PROMPT_SECRET not in message
    assert FAKE_API_KEY not in message


def test_adapter_metadata_is_safe(base_request: AgentRequest) -> None:
    adapter = SimulatedLLMAdapter()
    response = adapter.generate(LLMAdapterRequest(agent_request=base_request))
    meta = response.metadata
    assert meta.simulated is True
    assert "sk-live" not in meta.provider_name
    assert "sk-live" not in meta.model_name
    assert meta.latency_ms >= 0


def test_pipeline_with_disabled_external_adapter_fails_closed(
    base_request: AgentRequest,
    policy_path: Path,
    tmp_path: Path,
) -> None:
    adapter = create_llm_adapter(mode=LLMAdapterMode.DISABLED_EXTERNAL)
    pipeline = ControlPlanePipeline(
        policy_path,
        AuditLogger(tmp_path / "audit.jsonl"),
        llm_adapter=adapter,
    )
    with pytest.raises(LLMAdapterError):
        pipeline.run_protected(base_request)


def test_demo_still_works() -> None:
    run_demo()


def test_create_llm_adapter_factory_modes() -> None:
    assert isinstance(
        create_llm_adapter(mode=LLMAdapterMode.SIMULATED),
        SimulatedLLMAdapter,
    )
    assert isinstance(
        create_llm_adapter(mode=LLMAdapterMode.DISABLED_EXTERNAL),
        DisabledExternalLLMAdapter,
    )
