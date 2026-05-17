"""FastAPI local demo API for the control plane."""

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.models import AgentRequest, RetrievedChunk
from agent_control_plane.pipeline import ControlPlanePipeline

app = FastAPI(
    title="LLM Agent Control Plane Lab",
    description="Defensive reference API; simulated tools only.",
    version="0.1.0",
)

_POLICY_PATH = Path(__file__).resolve().parents[2] / "policies" / "default.yaml"
_AUDIT_PATH = Path(__file__).resolve().parents[2] / "audit_logs" / "api_events.jsonl"
_pipeline = ControlPlanePipeline(_POLICY_PATH, AuditLogger(_AUDIT_PATH))


class RunRequestBody(BaseModel):
    """HTTP body for running a protected pipeline turn."""

    request_id: str
    user_id: str
    session_id: str
    tenant_id: str
    role: str = "user"
    human_approval: bool = False
    user_message: str
    scenario: str = "safe_read"
    path: str = Field(default="protected", pattern="^(protected|vulnerable)$")
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/run")
def run_turn(body: RunRequestBody) -> dict[str, object]:
    """Execute one agent turn through the selected path."""
    request = AgentRequest(
        request_id=body.request_id,
        user_id=body.user_id,
        session_id=body.session_id,
        tenant_id=body.tenant_id,
        role=body.role,
        human_approval=body.human_approval,
        user_message=body.user_message,
        scenario=body.scenario,
        retrieved_chunks=body.retrieved_chunks,
    )
    if body.path == "vulnerable":
        result = _pipeline.run_vulnerable(request)
    else:
        result = _pipeline.run_protected(request)
    return result.model_dump()
