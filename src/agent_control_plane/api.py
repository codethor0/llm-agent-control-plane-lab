"""FastAPI local demo API for the control plane."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from agent_control_plane.audit_logger import AuditLogger
from agent_control_plane.config import (
    AppConfig,
    ConfigurationError,
    load_config_from_env,
    production_error_detail,
)
from agent_control_plane.llm_adapter import create_llm_adapter_from_config
from agent_control_plane.models import AgentRequest, RetrievedChunk
from agent_control_plane.observability import normalize_correlation_id, write_operational_audit
from agent_control_plane.pipeline import ControlPlanePipeline


class RunRequestBody(BaseModel):
    """HTTP body for running a protected pipeline turn."""

    request_id: str
    correlation_id: str | None = None
    user_id: str
    session_id: str
    tenant_id: str
    role: str = "user"
    human_approval: bool = False
    user_message: str
    scenario: str = "safe_read"
    path: str = Field(default="protected", pattern="^(protected|vulnerable)$")
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured maximum."""

    def __init__(
        self,
        app: ASGIApp,
        max_body_bytes: int,
        audit_logger: AuditLogger,
    ) -> None:
        super().__init__(app)
        self._max_body_bytes = max_body_bytes
        self._audit = audit_logger

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    size = int(content_length)
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "invalid_content_length"},
                    )
                if size > self._max_body_bytes:
                    correlation_id = normalize_correlation_id(
                        request.headers.get("X-Correlation-ID"),
                        fallback="api-body-limit",
                    )
                    write_operational_audit(
                        self._audit,
                        event_type="request_body_limit_blocked",
                        correlation_id=correlation_id,
                        request_id=correlation_id,
                        stage="api_middleware",
                        policy_reason="request_entity_too_large",
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "request_entity_too_large"},
                    )
        return await call_next(request)


def _extract_api_key(
    x_api_key: str | None,
    authorization: str | None,
) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return token if token else None
    return None


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Build the FastAPI application with deployment guardrails."""
    cfg = config or load_config_from_env()
    cfg.validate()

    cfg.audit_log_dir.mkdir(parents=True, exist_ok=True)
    audit_path = cfg.audit_log_dir / "api_events.jsonl"
    audit_logger = AuditLogger(audit_path)

    provenance_key: bytes | None = None
    if cfg.enable_strict_provenance:
        provenance_key = cfg.load_provenance_hmac_key()

    pipeline = ControlPlanePipeline(
        cfg.policy_path,
        audit_logger,
        require_provenance_signature=cfg.enable_strict_provenance,
        provenance_hmac_key=provenance_key,
        require_approval_token=cfg.require_approval_token,
        llm_adapter=create_llm_adapter_from_config(cfg),
    )

    app = FastAPI(
        title="LLM Agent Control Plane Lab",
        description="Defensive reference API; simulated tools only.",
        version="0.1.0",
    )

    app.state.config = cfg
    app.state.pipeline = pipeline
    app.state.audit_logger = audit_logger

    if cfg.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cfg.allowed_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-Correlation-ID"],
        )

    app.add_middleware(
        MaxBodySizeMiddleware,
        max_body_bytes=cfg.max_request_body_bytes,
        audit_logger=audit_logger,
    )

    def require_api_key(
        request: Request,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        if not cfg.require_api_auth:
            return
        presented = _extract_api_key(x_api_key, authorization)
        if presented is None or presented not in cfg.api_keys:
            correlation_id = normalize_correlation_id(
                request.headers.get("X-Correlation-ID"),
                fallback="api-unauthenticated",
            )
            write_operational_audit(
                audit_logger,
                event_type="api_auth_failure",
                correlation_id=correlation_id,
                request_id=correlation_id,
                stage="api_auth",
                policy_reason="unauthorized",
            )
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        if isinstance(exc, HTTPException):
            detail = exc.detail if isinstance(exc.detail, str) else "error"
            return JSONResponse(status_code=exc.status_code, content={"detail": detail})
        payload = production_error_detail(cfg, exc)
        return JSONResponse(status_code=500, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        if cfg.enable_debug_errors:
            return JSONResponse(status_code=422, content={"detail": exc.errors()})
        return JSONResponse(status_code=422, content={"detail": "validation_error"})

    @app.get("/health")
    def health() -> dict[str, str]:
        """Health check endpoint (no authentication required)."""
        return {"status": "ok", "mode": cfg.environment_mode.value}

    @app.post("/run", dependencies=[Depends(require_api_key)])
    def run_turn(
        body: RunRequestBody,
        x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-ID")] = None,
    ) -> dict[str, object]:
        """Execute one agent turn through the selected path."""
        correlation_id = normalize_correlation_id(
            body.correlation_id or x_correlation_id,
            fallback=body.request_id,
        )
        request = AgentRequest(
            request_id=body.request_id,
            correlation_id=correlation_id,
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
            result = pipeline.run_vulnerable(request)
        else:
            result = pipeline.run_protected(request)
        return result.model_dump()

    return app


_app_instance: FastAPI | None = None


def get_app() -> FastAPI:
    """Return the default application instance (lazy initialization)."""
    global _app_instance
    if _app_instance is None:
        try:
            _app_instance = create_app(load_config_from_env())
        except ConfigurationError as exc:
            raise RuntimeError(str(exc)) from exc
    return _app_instance


class _LazyASGIApp:
    """Defer app construction until the first ASGI request (writable audit dir)."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await get_app()(scope, receive, send)


app: ASGIApp = _LazyASGIApp()
