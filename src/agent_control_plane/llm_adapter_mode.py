"""LLM adapter mode enum (no imports from config or adapter implementation)."""

from enum import StrEnum


class LLMAdapterMode(StrEnum):
    """How the control plane obtains candidate model output."""

    SIMULATED = "simulated"
    DISABLED_EXTERNAL = "disabled_external"
