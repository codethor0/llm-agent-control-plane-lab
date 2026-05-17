"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.models import (
    AgentRequest,
    ContextTrust,
    Provenance,
    ProvenanceSource,
)
from agent_control_plane.pipeline import ControlPlanePipeline


@pytest.fixture
def policy_path() -> Path:
    return Path(__file__).resolve().parents[1] / "policies" / "default.yaml"


@pytest.fixture
def audit_logger(tmp_path: Path) -> AuditLogger:
    return AuditLogger(tmp_path / "audit.jsonl")


@pytest.fixture
def pipeline(policy_path: Path, audit_logger: AuditLogger) -> ControlPlanePipeline:
    return ControlPlanePipeline(policy_path, audit_logger)


@pytest.fixture
def base_request() -> AgentRequest:
    return AgentRequest(
        request_id="req-1",
        user_id="user-1",
        session_id="sess-1",
        tenant_id="tenant-a",
        role="user",
        human_approval=False,
        user_message="Please help.",
        scenario="safe_read",
    )


@pytest.fixture
def trusted_provenance() -> Provenance:
    return Provenance(
        source=ProvenanceSource.MODEL,
        trust=ContextTrust.TRUSTED,
        context_ids=["model-turn"],
    )
