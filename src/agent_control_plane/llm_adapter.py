"""Safe LLM adapter boundary: candidate model output only, never authorized actions."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from agent_control_plane.agent_core import run_simulated_agent
from agent_control_plane.llm_adapter_mode import LLMAdapterMode
from agent_control_plane.models import AgentRequest, ModelTurnResult, ToolCallPayload

__all__ = [
    "DisabledExternalLLMAdapter",
    "LLMAdapter",
    "LLMAdapterError",
    "LLMAdapterMetadata",
    "LLMAdapterMode",
    "LLMAdapterRequest",
    "LLMAdapterResponse",
    "SimulatedLLMAdapter",
    "create_llm_adapter",
    "create_llm_adapter_from_config",
    "to_model_turn_result",
]


class LLMAdapterError(RuntimeError):
    """Adapter failure. Messages must not include secrets, prompts, or API keys."""


@dataclass(frozen=True, slots=True)
class LLMAdapterMetadata:
    """Non-sensitive metadata about an adapter invocation."""

    provider_name: str
    model_name: str
    simulated: bool
    latency_ms: int


class LLMAdapterRequest(BaseModel):
    """Input to an LLM adapter (untrusted user and retrieved context only)."""

    agent_request: AgentRequest


class LLMAdapterResponse(BaseModel):
    """Untrusted candidate output from an adapter. Not authorized for tools or side effects."""

    natural_language: str
    tool_call: ToolCallPayload | None = None
    metadata: LLMAdapterMetadata


@runtime_checkable
class LLMAdapter(Protocol):
    """Produces untrusted candidate model output. Must not call tools or authorize actions."""

    def generate(self, request: LLMAdapterRequest) -> LLMAdapterResponse:
        """Return candidate text and optional structured tool call (still untrusted)."""
        ...


class SimulatedLLMAdapter:
    """
    Offline deterministic adapter wrapping the lab agent core.

    Invariant: no network I/O; output is untrusted candidate content only.
    """

    provider_name: str = "simulated"

    def generate(self, request: LLMAdapterRequest) -> LLMAdapterResponse:
        started = time.perf_counter()
        turn = run_simulated_agent(request.agent_request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return LLMAdapterResponse(
            natural_language=turn.natural_language,
            tool_call=turn.tool_call,
            metadata=LLMAdapterMetadata(
                provider_name=self.provider_name,
                model_name=request.agent_request.model,
                simulated=True,
                latency_ms=elapsed_ms,
            ),
        )


class DisabledExternalLLMAdapter:
    """
    Fail-closed stub for future external providers.

    No network calls are performed. Live integration is not implemented in this repository.
    """

    def __init__(
        self,
        *,
        provider_name: str = "external",
        model_name: str = "disabled",
    ) -> None:
        self._provider_name = provider_name
        self._model_name = model_name

    def generate(self, request: LLMAdapterRequest) -> LLMAdapterResponse:
        _ = request
        raise LLMAdapterError(
            f"external LLM adapter is disabled (provider={self._provider_name!r}); "
            "no live provider implementation is available"
        )


def to_model_turn_result(response: LLMAdapterResponse) -> ModelTurnResult:
    """Convert adapter output into pipeline model turn (still untrusted)."""
    return ModelTurnResult(
        natural_language=response.natural_language,
        tool_call=response.tool_call,
    )


def create_llm_adapter(
    *,
    mode: LLMAdapterMode = LLMAdapterMode.SIMULATED,
    provider_name: str | None = None,
    model_name: str | None = None,
) -> LLMAdapter:
    """Build an adapter for the given mode (default: simulated)."""
    if mode is LLMAdapterMode.DISABLED_EXTERNAL:
        return DisabledExternalLLMAdapter(
            provider_name=provider_name or "external",
            model_name=model_name or "disabled",
        )
    return SimulatedLLMAdapter()


def create_llm_adapter_from_config(config: object) -> LLMAdapter:
    """Factory using AppConfig fields when available."""
    from agent_control_plane.config import AppConfig

    if not isinstance(config, AppConfig):
        return SimulatedLLMAdapter()
    return create_llm_adapter(
        mode=config.llm_adapter_mode,
        provider_name=config.llm_provider_name,
        model_name=config.llm_model_name,
    )
