"""Policy document types (shared by policy engine, provenance, and approval gate)."""

from pydantic import BaseModel, Field

from agent_control_plane.models import RiskLevel


class ToolPolicy(BaseModel):
    """Policy entry for a single tool."""

    enabled: bool = False
    risk_level: RiskLevel = RiskLevel.HIGH
    external_effect: bool = False
    destructive: bool = False
    requires_human_approval: bool = True
    allowed_roles: list[str] = Field(default_factory=list)


class PolicyDocument(BaseModel):
    """Parsed policy file."""

    default_decision: str = "deny"
    tools: dict[str, ToolPolicy] = Field(default_factory=dict)
    tenant_isolation: str = "strict"
