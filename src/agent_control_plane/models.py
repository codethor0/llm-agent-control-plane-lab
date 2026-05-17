"""Shared domain models for the control plane."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ContextTrust(StrEnum):
    """Trust classification for context used in authorization."""

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class ProvenanceSource(StrEnum):
    """Origin of a tool authorization signal (declarative; not attested)."""

    USER = "user"
    MODEL = "model"
    RETRIEVED = "retrieved"
    SYSTEM = "system"
    EXTERNAL = "external"
    WEB = "web"
    EMAIL = "email"
    SUPPORT_TICKET = "support_ticket"
    INTERNAL_REVIEWED = "internal_reviewed"


class RiskLevel(StrEnum):
    """Policy-assigned risk for a tool."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetrievedChunk(BaseModel):
    """Untrusted-by-default retrieved evidence."""

    id: str
    content: str
    trust: ContextTrust = ContextTrust.UNTRUSTED
    tenant_id: str


class Provenance(BaseModel):
    """Provenance attached to a tool request; required for broker decisions."""

    source: ProvenanceSource
    trust: ContextTrust
    context_ids: list[str] = Field(default_factory=list)


class AgentRequest(BaseModel):
    """Inbound request context for a single agent turn."""

    request_id: str
    user_id: str
    session_id: str
    tenant_id: str
    role: str
    model: str = "simulated-v1"
    human_approval: bool = False
    user_message: str
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    scenario: str = "safe_read"


class ToolCallPayload(BaseModel):
    """Structured tool call emitted by the simulated model (untrusted)."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    target: str | None = None
    provenance: Provenance | None = None


class ModelTurnResult(BaseModel):
    """Untrusted output from the simulated agent core."""

    natural_language: str
    tool_call: ToolCallPayload | None = None


class PolicyDecision(BaseModel):
    """Deterministic policy evaluation result."""

    allowed: bool
    reason: str
    risk_level: RiskLevel | None = None
    requires_human_approval: bool = False
    external_effect: bool = False


class BrokerDecision(BaseModel):
    """Final broker authority decision."""

    allowed: bool
    reason: str
    policy_decision: PolicyDecision | None = None
    schema_valid: bool = True


class SimulationResult(BaseModel):
    """Result of safe simulated tool execution."""

    success: bool
    message: str
    simulated_output: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    """End-to-end pipeline outcome."""

    request_id: str
    path: str
    allowed: bool
    stage: str
    reason: str
    model_text: str = ""
    filtered_output: str = ""
    tool_executed: bool = False
    simulation: SimulationResult | None = None
