"""Production-oriented runtime configuration with fail-closed validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from agent_control_plane.llm_adapter import LLMAdapterMode


class EnvironmentMode(StrEnum):
    """Deployment environment profile."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class ConfigurationError(ValueError):
    """Invalid configuration. Messages must never include secret material."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"invalid integer for {name}") from exc


def _parse_origins(raw: str | None, default: list[str]) -> list[str]:
    if raw is None or raw.strip() == "":
        return list(default)
    return [part.strip() for part in raw.split(",") if part.strip()]


def _load_api_keys(*, keys_file: Path | None, inline_key: str | None) -> frozenset[str]:
    keys: set[str] = set()
    if inline_key and inline_key.strip():
        keys.add(inline_key.strip())
    if keys_file is not None:
        if not keys_file.is_file():
            raise ConfigurationError(f"API keys file not found: {keys_file.name}")
        for line in keys_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            keys.add(stripped)
    return frozenset(keys)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Typed application configuration for API and deployment guardrails."""

    environment_mode: EnvironmentMode
    require_api_auth: bool
    allowed_api_keys_file: Path | None
    allowed_origins: tuple[str, ...]
    max_request_body_bytes: int
    audit_log_dir: Path
    audit_retention_days: int
    enable_strict_provenance: bool
    provenance_hmac_key_file: Path | None
    require_approval_token: bool
    enable_rate_limit_guidance: bool
    enable_debug_errors: bool
    allow_live_external_tools: bool
    allow_shell_tools: bool
    llm_adapter_mode: LLMAdapterMode
    allow_live_llm_calls: bool
    llm_provider_name: str | None
    llm_model_name: str | None
    policy_path: Path
    _api_keys: frozenset[str]

    @property
    def api_keys(self) -> frozenset[str]:
        return self._api_keys

    def validate(self) -> None:
        """Fail closed on unsafe or incomplete production settings."""
        errors: list[str] = []

        if self.max_request_body_bytes < 1024:
            errors.append("max_request_body_bytes must be at least 1024")
        if self.max_request_body_bytes > 10_485_760:
            errors.append("max_request_body_bytes must not exceed 10485760")
        if self.audit_retention_days < 1:
            errors.append("audit_retention_days must be at least 1")
        if self.audit_retention_days > 3650:
            errors.append("audit_retention_days must not exceed 3650")
        if not self.policy_path.is_file():
            errors.append(f"policy file not found: {self.policy_path.name}")

        if self.allow_live_external_tools:
            errors.append("allow_live_external_tools must remain disabled")
        if self.allow_shell_tools:
            errors.append("allow_shell_tools must remain disabled")

        if self.allow_live_llm_calls:
            errors.append("live LLM calls are not implemented; keep allow_live_llm_calls false")

        if self.environment_mode is EnvironmentMode.PRODUCTION:
            if not self.require_api_auth:
                errors.append("production requires API authentication")
            if not self._api_keys:
                errors.append("production requires at least one API key")
            if not self.allowed_origins:
                errors.append("production requires explicit allowed_origins")
            if "*" in self.allowed_origins:
                errors.append("production disallows wildcard CORS origins")
            if self.enable_debug_errors:
                errors.append("production disallows debug error responses")
            if self.enable_strict_provenance and self.provenance_hmac_key_file is None:
                errors.append("production strict provenance requires provenance_hmac_key_file")
            if (
                self.enable_strict_provenance
                and self.provenance_hmac_key_file is not None
                and not self.provenance_hmac_key_file.is_file()
            ):
                errors.append(
                    f"provenance key file not found: {self.provenance_hmac_key_file.name}"
                )

        if self.require_api_auth and not self._api_keys:
            errors.append("require_api_auth is set but no API keys are configured")

        if errors:
            raise ConfigurationError("; ".join(errors))

    def load_provenance_hmac_key(self) -> bytes | None:
        if self.provenance_hmac_key_file is None:
            return None
        raw = self.provenance_hmac_key_file.read_bytes()
        if not raw:
            raise ConfigurationError(
                f"provenance key file is empty: {self.provenance_hmac_key_file.name}"
            )
        return raw


def load_config_from_env() -> AppConfig:
    """Load configuration from environment variables (safe defaults for local demo)."""
    mode_raw = os.environ.get("ACP_ENVIRONMENT", "local").strip().lower()
    try:
        mode = EnvironmentMode(mode_raw)
    except ValueError as exc:
        raise ConfigurationError(f"invalid ACP_ENVIRONMENT: {mode_raw}") from exc

    repo_root = Path(__file__).resolve().parents[2]
    default_policy = repo_root / "policies" / "default.yaml"
    default_audit_dir = repo_root / "audit_logs"

    keys_file_raw = os.environ.get("ACP_ALLOWED_API_KEYS_FILE")
    keys_file = Path(keys_file_raw).expanduser() if keys_file_raw else None
    inline_key = os.environ.get("ACP_API_KEY")

    if mode is EnvironmentMode.LOCAL:
        default_origins = ["http://127.0.0.1:8080", "http://localhost:8080"]
        default_require_auth = False
        default_debug = True
    elif mode is EnvironmentMode.TEST:
        default_origins = ["http://127.0.0.1:8080"]
        default_require_auth = False
        default_debug = True
    else:
        default_origins = []
        default_require_auth = True
        default_debug = False

    origins = tuple(_parse_origins(os.environ.get("ACP_ALLOWED_ORIGINS"), default_origins))

    policy_path = Path(
        os.environ.get("ACP_POLICY_PATH", os.environ.get("POLICY_PATH", str(default_policy)))
    ).expanduser()
    audit_log_dir = Path(os.environ.get("ACP_AUDIT_LOG_DIR", str(default_audit_dir))).expanduser()

    provenance_key_file_raw = os.environ.get("ACP_PROVENANCE_HMAC_KEY_FILE")
    provenance_key_file = (
        Path(provenance_key_file_raw).expanduser() if provenance_key_file_raw else None
    )

    api_keys = _load_api_keys(keys_file=keys_file, inline_key=inline_key)

    adapter_mode_raw = os.environ.get("ACP_LLM_ADAPTER_MODE", "simulated").strip().lower()
    try:
        llm_adapter_mode = LLMAdapterMode(adapter_mode_raw)
    except ValueError as exc:
        raise ConfigurationError(f"invalid ACP_LLM_ADAPTER_MODE: {adapter_mode_raw}") from exc

    provider_raw = os.environ.get("ACP_LLM_PROVIDER_NAME")
    model_raw = os.environ.get("ACP_LLM_MODEL_NAME")

    return AppConfig(
        environment_mode=mode,
        require_api_auth=_env_bool("ACP_REQUIRE_API_AUTH", default_require_auth),
        allowed_api_keys_file=keys_file,
        allowed_origins=origins,
        max_request_body_bytes=_env_int("ACP_MAX_REQUEST_BODY_BYTES", 1_048_576),
        audit_log_dir=audit_log_dir,
        audit_retention_days=_env_int("ACP_AUDIT_RETENTION_DAYS", 90),
        enable_strict_provenance=_env_bool("ACP_ENABLE_STRICT_PROVENANCE", False),
        provenance_hmac_key_file=provenance_key_file,
        require_approval_token=_env_bool("ACP_REQUIRE_APPROVAL_TOKEN", False),
        enable_rate_limit_guidance=_env_bool("ACP_ENABLE_RATE_LIMIT_GUIDANCE", True),
        enable_debug_errors=_env_bool("ACP_ENABLE_DEBUG_ERRORS", default_debug),
        allow_live_external_tools=_env_bool("ACP_ALLOW_LIVE_EXTERNAL_TOOLS", False),
        allow_shell_tools=_env_bool("ACP_ALLOW_SHELL_TOOLS", False),
        llm_adapter_mode=llm_adapter_mode,
        allow_live_llm_calls=_env_bool("ACP_ALLOW_LIVE_LLM_CALLS", False),
        llm_provider_name=provider_raw.strip() if provider_raw else None,
        llm_model_name=model_raw.strip() if model_raw else None,
        policy_path=policy_path,
        _api_keys=api_keys,
    )


def production_error_detail(config: AppConfig, exc: Exception) -> dict[str, str]:
    """Build a safe error payload that never includes secrets."""
    if config.enable_debug_errors:
        return {"detail": str(exc), "error_type": type(exc).__name__}
    return {"detail": "internal_error"}
