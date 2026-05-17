"""Tool broker: authority boundary between untrusted model output and execution."""

from agent_control_plane.approval_gate import evaluate_approval_gate
from agent_control_plane.models import AgentRequest, BrokerDecision, ToolCallPayload
from agent_control_plane.policy_engine import evaluate_policy
from agent_control_plane.policy_types import PolicyDocument
from agent_control_plane.provenance_integrity import (
    LAB_DEMO_HMAC_KEY,
    verify_provenance_integrity,
)
from agent_control_plane.schemas import validate_tool_call_payload


def broker_tool_request(
    request: AgentRequest,
    policy: PolicyDocument,
    tool_call: ToolCallPayload,
    *,
    require_provenance_signature: bool = False,
    provenance_hmac_key: bytes | None = None,
) -> BrokerDecision:
    """
    Decide whether a tool request may proceed to simulation.

    Invariant: the broker is the authority boundary; schema validation alone never allows
    execution. Policy and provenance run first; the approval gate runs before allow.
    """
    schema_valid, schema_reason = validate_tool_call_payload(tool_call)
    if not schema_valid:
        return BrokerDecision(
            allowed=False,
            reason=schema_reason,
            schema_valid=False,
        )

    hmac_key = provenance_hmac_key if provenance_hmac_key is not None else LAB_DEMO_HMAC_KEY
    integrity_ok, integrity_reason = verify_provenance_integrity(
        tool_call.provenance,
        hmac_key,
        require_signature=require_provenance_signature,
    )
    if not integrity_ok:
        return BrokerDecision(
            allowed=False,
            reason=integrity_reason,
            schema_valid=True,
        )

    policy_decision = evaluate_policy(policy, request, tool_call)
    if not policy_decision.allowed:
        return BrokerDecision(
            allowed=False,
            reason=policy_decision.reason,
            policy_decision=policy_decision,
            schema_valid=True,
        )

    tool_policy = policy.tools[tool_call.tool_name]
    approval = evaluate_approval_gate(request, tool_policy)
    if not approval.allowed:
        return BrokerDecision(
            allowed=False,
            reason=approval.reason,
            policy_decision=policy_decision,
            schema_valid=True,
        )

    return BrokerDecision(
        allowed=True,
        reason=policy_decision.reason,
        policy_decision=policy_decision,
        schema_valid=True,
    )
