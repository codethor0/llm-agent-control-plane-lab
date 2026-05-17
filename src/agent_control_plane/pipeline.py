"""End-to-end control plane pipeline: protected and vulnerable paths."""

from pathlib import Path

from agent_control_plane.agent_core import run_simulated_agent
from agent_control_plane.audit_logger import AuditEvent, AuditLogger
from agent_control_plane.models import (
    AgentRequest,
    PipelineResult,
    PolicyDecision,
    Provenance,
    ToolCallPayload,
)
from agent_control_plane.output_filter import filter_model_output
from agent_control_plane.policy_engine import load_policy
from agent_control_plane.simulator import simulate_tool_execution, simulate_vulnerable_execution
from agent_control_plane.tool_broker import broker_tool_request


class ControlPlanePipeline:
    """Orchestrates the defensive control plane for a single agent turn."""

    def __init__(
        self,
        policy_path: Path,
        audit_logger: AuditLogger,
        *,
        require_provenance_signature: bool = False,
        provenance_hmac_key: bytes | None = None,
    ) -> None:
        self._policy_path = policy_path
        self._audit = audit_logger
        self._require_provenance_signature = require_provenance_signature
        self._provenance_hmac_key = provenance_hmac_key

    def run_protected(self, request: AgentRequest) -> PipelineResult:
        """
        Run the full control plane: model output is untrusted until broker and filters approve.

        Invariant: protected path enforces schema validation, broker, policy,
        approval, output filter, and audit.
        """
        policy = load_policy(self._policy_path)
        model_turn = run_simulated_agent(request)

        output_result = filter_model_output(model_turn.natural_language)
        if not output_result.allowed:
            self._audit.write(
                _audit_event(
                    request,
                    event_type="output_filter_blocked",
                    stage="output_filter",
                    allowed=False,
                    policy_reason=output_result.reason,
                    tool_name=None,
                    target=None,
                    risk_level=None,
                    human_approval_required=False,
                    contains_sensitive=True,
                )
            )
            return PipelineResult(
                request_id=request.request_id,
                path="protected",
                allowed=False,
                stage="output_filter",
                reason=output_result.reason,
                model_text=model_turn.natural_language,
                filtered_output="",
            )

        if model_turn.tool_call is None:
            self._audit.write(
                _audit_event(
                    request,
                    event_type="model_response_allowed",
                    stage="complete",
                    allowed=True,
                    policy_reason="no_tool_call",
                    tool_name=None,
                    target=None,
                    risk_level=None,
                    human_approval_required=False,
                    contains_sensitive=False,
                )
            )
            return PipelineResult(
                request_id=request.request_id,
                path="protected",
                allowed=True,
                stage="complete",
                reason="no_tool_call",
                model_text=model_turn.natural_language,
                filtered_output=output_result.filtered_text,
            )

        tool_call = model_turn.tool_call
        broker_decision = broker_tool_request(
            request,
            policy,
            tool_call,
            require_provenance_signature=self._require_provenance_signature,
            provenance_hmac_key=self._provenance_hmac_key,
        )

        if not broker_decision.schema_valid:
            self._audit.write(
                _audit_event_for_tool(
                    request,
                    tool_call,
                    event_type="schema_validation_failed",
                    stage="schema_validation",
                    allowed=False,
                    policy_reason=broker_decision.reason,
                    human_approval_required=False,
                )
            )
            return PipelineResult(
                request_id=request.request_id,
                path="protected",
                allowed=False,
                stage="schema_validation",
                reason=broker_decision.reason,
                model_text=model_turn.natural_language,
                filtered_output=output_result.filtered_text,
            )

        pd = broker_decision.policy_decision
        if not broker_decision.allowed:
            event_type = _blocked_event_type(broker_decision.reason)
            self._audit.write(
                _audit_event_for_tool(
                    request,
                    tool_call,
                    event_type=event_type,
                    stage="tool_broker",
                    allowed=False,
                    policy_reason=broker_decision.reason,
                    human_approval_required=_approval_required_from_reason(
                        broker_decision.reason,
                        pd,
                    ),
                    policy_decision=pd,
                )
            )
            return PipelineResult(
                request_id=request.request_id,
                path="protected",
                allowed=False,
                stage="tool_broker",
                reason=broker_decision.reason,
                model_text=model_turn.natural_language,
                filtered_output=output_result.filtered_text,
            )

        simulation = simulate_tool_execution(request, tool_call)
        self._audit.write(
            _audit_event_for_tool(
                request,
                tool_call,
                event_type="tool_allowed",
                stage="simulation",
                allowed=True,
                policy_reason=broker_decision.reason,
                human_approval_required=request.human_approval,
                policy_decision=pd,
            )
        )
        return PipelineResult(
            request_id=request.request_id,
            path="protected",
            allowed=True,
            stage="simulation",
            reason=broker_decision.reason,
            model_text=model_turn.natural_language,
            filtered_output=output_result.filtered_text,
            tool_executed=True,
            simulation=simulation,
        )

    def run_vulnerable(self, request: AgentRequest) -> PipelineResult:
        """
        Demonstrate an agent path without broker/policy (simulation labeled unsafe only).

        Invariant: vulnerable path never performs real shell, network, or external execution.
        """
        model_turn = run_simulated_agent(request)
        if model_turn.tool_call is None:
            return PipelineResult(
                request_id=request.request_id,
                path="vulnerable",
                allowed=True,
                stage="complete",
                reason="no_tool_call_vulnerable_path",
                model_text=model_turn.natural_language,
                filtered_output=model_turn.natural_language,
            )

        unsafe = simulate_vulnerable_execution(model_turn.tool_call)
        self._audit.write(
            AuditEvent(
                event_type="vulnerable_path_simulation",
                request_id=request.request_id,
                user_id=request.user_id,
                session_id=request.session_id,
                tenant_id=request.tenant_id,
                model=request.model,
                tool_name=model_turn.tool_call.tool_name,
                target=model_turn.tool_call.target,
                risk_level="simulated",
                source_context_ids=_context_ids(model_turn.tool_call.provenance),
                retrieved_context_trust=_provenance_trust(model_turn.tool_call.provenance),
                policy_decision="bypassed",
                policy_reason=str(unsafe.get("unsafe_decision", "simulated")),
                contains_sensitive_data=False,
                human_approval_required=False,
                stage="vulnerable_simulation",
                allowed=True,
            )
        )
        return PipelineResult(
            request_id=request.request_id,
            path="vulnerable",
            allowed=True,
            stage="vulnerable_simulation",
            reason=str(unsafe.get("unsafe_decision")),
            model_text=model_turn.natural_language,
            filtered_output=model_turn.natural_language,
            tool_executed=False,
            simulation=None,
        )


def _blocked_event_type(reason: str) -> str:
    if reason == "cross_tenant_target_denied":
        return "cross_tenant_blocked"
    if "human_approval_required" in reason:
        return "approval_denied"
    if reason == "missing_provenance_denied":
        return "provenance_denied"
    if "cannot_authorize" in reason or "provenance" in reason:
        return "provenance_denied"
    return "tool_blocked"


def _approval_required_from_reason(
    reason: str,
    policy_decision: PolicyDecision | None,
) -> bool:
    return "human_approval_required" in reason or bool(
        policy_decision and policy_decision.requires_human_approval
    )


def _risk_level_str(policy_decision: PolicyDecision | None) -> str | None:
    if policy_decision and policy_decision.risk_level:
        return policy_decision.risk_level.value
    return None


def _context_ids(provenance: Provenance | None) -> list[str]:
    if provenance is None:
        return []
    return list(provenance.context_ids)


def _provenance_trust(provenance: Provenance | None) -> str | None:
    if provenance is None:
        return None
    return provenance.trust.value


def _audit_event(
    request: AgentRequest,
    *,
    event_type: str,
    stage: str,
    allowed: bool,
    policy_reason: str,
    tool_name: str | None,
    target: str | None,
    risk_level: str | None,
    human_approval_required: bool,
    contains_sensitive: bool,
    policy_decision: str = "deny",
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        request_id=request.request_id,
        user_id=request.user_id,
        session_id=request.session_id,
        tenant_id=request.tenant_id,
        model=request.model,
        tool_name=tool_name,
        target=target,
        risk_level=risk_level,
        source_context_ids=[],
        retrieved_context_trust=None,
        policy_decision=policy_decision,
        policy_reason=policy_reason,
        contains_sensitive_data=contains_sensitive,
        human_approval_required=human_approval_required,
        stage=stage,
        allowed=allowed,
    )


def _audit_event_for_tool(
    request: AgentRequest,
    tool_call: ToolCallPayload,
    *,
    event_type: str,
    stage: str,
    allowed: bool,
    policy_reason: str,
    human_approval_required: bool,
    policy_decision: PolicyDecision | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        request_id=request.request_id,
        user_id=request.user_id,
        session_id=request.session_id,
        tenant_id=request.tenant_id,
        model=request.model,
        tool_name=tool_call.tool_name,
        target=tool_call.target,
        risk_level=_risk_level_str(policy_decision),
        source_context_ids=_context_ids(tool_call.provenance),
        retrieved_context_trust=_provenance_trust(tool_call.provenance),
        policy_decision="allow" if allowed else "deny",
        policy_reason=policy_reason,
        contains_sensitive_data=False,
        human_approval_required=human_approval_required,
        stage=stage,
        allowed=allowed,
    )
