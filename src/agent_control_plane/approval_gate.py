"""Human approval gate for high-impact tool actions."""

from dataclasses import dataclass

from agent_control_plane.approval_tokens import verify_approval_token
from agent_control_plane.models import AgentRequest, ToolCallPayload
from agent_control_plane.policy_types import ToolPolicy


@dataclass(frozen=True)
class ApprovalGateResult:
    """Result of the human approval gate (separate from policy structure checks)."""

    allowed: bool
    reason: str
    approval_required: bool
    approval_id: str | None = None
    approver_id: str | None = None
    approval_decision: str | None = None
    approval_reason: str | None = None
    approval_token_valid: bool | None = None
    approval_token_failure_reason: str | None = None


def evaluate_approval_gate(
    request: AgentRequest,
    tool_policy: ToolPolicy,
    tool_call: ToolCallPayload,
    *,
    require_approval_token: bool = False,
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
            approval_decision="not_required",
        )

    risk_level = tool_policy.risk_level.value
    token = request.approval_token

    if token is not None or require_approval_token:
        if token is None:
            reason = "approval_token_missing"
            return ApprovalGateResult(
                allowed=False,
                reason=reason,
                approval_required=True,
                approval_decision="denied",
                approval_token_valid=False,
                approval_token_failure_reason=reason,
            )
        ok, reason = verify_approval_token(token, request, tool_call, risk_level)
        if not ok:
            return ApprovalGateResult(
                allowed=False,
                reason=reason,
                approval_required=True,
                approval_id=token.approval_id,
                approver_id=token.approver_id,
                approval_decision="denied",
                approval_reason=token.approval_reason,
                approval_token_valid=False,
                approval_token_failure_reason=reason,
            )
        return ApprovalGateResult(
            allowed=True,
            reason="approval_token_granted",
            approval_required=True,
            approval_id=token.approval_id,
            approver_id=token.approver_id,
            approval_decision="granted",
            approval_reason=token.approval_reason,
            approval_token_valid=True,
        )

    if not request.human_approval:
        if tool_policy.external_effect or tool_policy.destructive:
            reason = "human_approval_required_for_high_impact_action"
            return ApprovalGateResult(
                allowed=False,
                reason=reason,
                approval_required=True,
                approval_decision="denied",
                approval_token_valid=False,
                approval_token_failure_reason=reason,
            )
        reason = "human_approval_required_by_policy"
        return ApprovalGateResult(
            allowed=False,
            reason=reason,
            approval_required=True,
            approval_decision="denied",
            approval_token_valid=False,
            approval_token_failure_reason=reason,
        )

    return ApprovalGateResult(
        allowed=True,
        reason="human_approval_granted",
        approval_required=True,
        approval_decision="granted",
        approval_token_valid=None,
    )
