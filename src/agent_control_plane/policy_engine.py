"""Deterministic policy engine loading YAML rules; deny by default."""

from pathlib import Path
from typing import Any

import yaml

from agent_control_plane.models import AgentRequest, PolicyDecision, ToolCallPayload
from agent_control_plane.policy_types import PolicyDocument, ToolPolicy
from agent_control_plane.provenance import validate_provenance_for_tool


def load_policy(path: Path) -> PolicyDocument:
    """
    Load policy from YAML.

    Invariant: missing or invalid policy file results in deny-all behavior at evaluation time.
    """
    if not path.is_file():
        return PolicyDocument(default_decision="deny", tools={})
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return PolicyDocument(default_decision="deny", tools={})
    tools_raw = raw.get("tools", {})
    tools: dict[str, ToolPolicy] = {}
    if isinstance(tools_raw, dict):
        for name, cfg in tools_raw.items():
            if isinstance(cfg, dict):
                tools[name] = ToolPolicy.model_validate(cfg)
    return PolicyDocument(
        default_decision=str(raw.get("default_decision", "deny")),
        tools=tools,
        tenant_isolation=str(raw.get("tenant_isolation", "strict")),
    )


def evaluate_policy(
    policy: PolicyDocument,
    request: AgentRequest,
    tool_call: ToolCallPayload,
) -> PolicyDecision:
    """
    Evaluate whether a tool call is allowed by static policy.

    Invariant: default decision is deny; unknown and disabled tools are denied.
    """
    default_deny = policy.default_decision != "allow"

    tool_name = tool_call.tool_name
    tool_policy = policy.tools.get(tool_name)
    if tool_policy is None:
        return PolicyDecision(
            allowed=False,
            reason="unknown_tool_denied_by_policy",
            risk_level=None,
        )

    if not tool_policy.enabled:
        return PolicyDecision(
            allowed=False,
            reason="tool_disabled_by_policy",
            risk_level=tool_policy.risk_level,
            requires_human_approval=tool_policy.requires_human_approval,
            external_effect=tool_policy.external_effect,
        )

    if request.role not in tool_policy.allowed_roles:
        return PolicyDecision(
            allowed=False,
            reason="role_not_permitted_for_tool",
            risk_level=tool_policy.risk_level,
            requires_human_approval=tool_policy.requires_human_approval,
            external_effect=tool_policy.external_effect,
        )

    if policy.tenant_isolation == "strict" and tool_call.target != request.tenant_id:
        return PolicyDecision(
            allowed=False,
            reason="cross_tenant_target_denied",
            risk_level=tool_policy.risk_level,
            requires_human_approval=tool_policy.requires_human_approval,
            external_effect=tool_policy.external_effect,
        )

    provenance_ok, provenance_reason = validate_provenance_for_tool(
        tool_policy,
        tool_call.provenance,
    )
    if not provenance_ok:
        return PolicyDecision(
            allowed=False,
            reason=provenance_reason,
            risk_level=tool_policy.risk_level,
            requires_human_approval=tool_policy.requires_human_approval,
            external_effect=tool_policy.external_effect,
        )

    if default_deny:
        return PolicyDecision(
            allowed=True,
            reason="explicit_allow_after_policy_checks",
            risk_level=tool_policy.risk_level,
            requires_human_approval=tool_policy.requires_human_approval,
            external_effect=tool_policy.external_effect,
        )

    return PolicyDecision(
        allowed=False,
        reason="default_deny_policy",
        risk_level=tool_policy.risk_level,
    )
