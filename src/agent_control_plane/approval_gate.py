"""Human approval gate for high-impact tool actions."""

from dataclasses import dataclass

from agent_control_plane.models import AgentRequest
from agent_control_plane.policy_types import ToolPolicy


@dataclass(frozen=True)
class ApprovalGateResult:
    """Result of the human approval gate (separate from policy structure checks)."""

    allowed: bool
    reason: str
    approval_required: bool


def evaluate_approval_gate(
    request: AgentRequest,
    tool_policy: ToolPolicy,
) -> ApprovalGateResult:
    """
    Enforce human approval for high-impact tools after policy and provenance allow.

    Invariant: approval does not bypass broker or policy; it only gates execution when
    policy would otherwise permit the tool structurally.
    """
    approval_required = (
        tool_policy.requires_human_approval
        or tool_policy.external_effect
        or tool_policy.destructive
    )
    if not approval_required:
        return ApprovalGateResult(
            allowed=True,
            reason="approval_not_required",
            approval_required=False,
        )

    if not request.human_approval:
        if tool_policy.external_effect or tool_policy.destructive:
            return ApprovalGateResult(
                allowed=False,
                reason="human_approval_required_for_high_impact_action",
                approval_required=True,
            )
        return ApprovalGateResult(
            allowed=False,
            reason="human_approval_required_by_policy",
            approval_required=True,
        )

    return ApprovalGateResult(
        allowed=True,
        reason="human_approval_granted",
        approval_required=True,
    )
