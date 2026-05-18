"""Tests for production configuration validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_control_plane.config import (
    AppConfig,
    ConfigurationError,
    EnvironmentMode,
    load_config_from_env,
    production_error_detail,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "policies" / "default.yaml"
FAKE_API_KEY = "lab-fake-api-key-test-only"


def _local_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        environment_mode=EnvironmentMode.LOCAL,
        require_api_auth=False,
        allowed_api_keys_file=None,
        allowed_origins=("http://127.0.0.1:8080",),
        max_request_body_bytes=1_048_576,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=False,
        provenance_hmac_key_file=None,
        require_approval_token=False,
        enable_rate_limit_guidance=True,
        enable_debug_errors=True,
        allow_live_external_tools=False,
        allow_shell_tools=False,
        policy_path=POLICY_PATH,
        _api_keys=frozenset(),
    )


def _production_config(
    tmp_path: Path,
    *,
    api_keys: frozenset[str] | None = None,
    allowed_origins: tuple[str, ...] = ("https://app.example.invalid",),
    require_api_auth: bool = True,
    enable_debug_errors: bool = False,
    allow_live_external_tools: bool = False,
    allow_shell_tools: bool = False,
    enable_strict_provenance: bool = False,
    provenance_hmac_key_file: Path | None = None,
    require_approval_token: bool = False,
) -> AppConfig:
    keys = api_keys if api_keys is not None else frozenset({FAKE_API_KEY})
    return AppConfig(
        environment_mode=EnvironmentMode.PRODUCTION,
        require_api_auth=require_api_auth,
        allowed_api_keys_file=None,
        allowed_origins=allowed_origins,
        max_request_body_bytes=1_048_576,
        audit_log_dir=tmp_path / "audit",
        audit_retention_days=90,
        enable_strict_provenance=enable_strict_provenance,
        provenance_hmac_key_file=provenance_hmac_key_file,
        require_approval_token=require_approval_token,
        enable_rate_limit_guidance=True,
        enable_debug_errors=enable_debug_errors,
        allow_live_external_tools=allow_live_external_tools,
        allow_shell_tools=allow_shell_tools,
        policy_path=POLICY_PATH,
        _api_keys=keys,
    )


def test_local_config_loads_safely(tmp_path: Path) -> None:
    cfg = _local_config(tmp_path)
    cfg.validate()


def test_production_config_without_auth_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, require_api_auth=False)
    with pytest.raises(ConfigurationError, match="production requires API authentication"):
        cfg.validate()


def test_production_config_without_api_keys_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, api_keys=frozenset())
    with pytest.raises(ConfigurationError, match="at least one API key"):
        cfg.validate()


def test_production_config_wildcard_cors_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, allowed_origins=("*",))
    with pytest.raises(ConfigurationError, match="wildcard CORS"):
        cfg.validate()


def test_production_config_empty_origins_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, allowed_origins=())
    with pytest.raises(ConfigurationError, match="explicit allowed_origins"):
        cfg.validate()


def test_production_config_debug_errors_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, enable_debug_errors=True)
    with pytest.raises(ConfigurationError, match="debug error"):
        cfg.validate()


def test_production_config_live_external_tools_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, allow_live_external_tools=True)
    with pytest.raises(ConfigurationError, match="allow_live_external_tools"):
        cfg.validate()


def test_production_config_shell_tools_fails(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, allow_shell_tools=True)
    with pytest.raises(ConfigurationError, match="allow_shell_tools"):
        cfg.validate()


def test_production_strict_provenance_passes_with_key_file(tmp_path: Path) -> None:
    key_file = tmp_path / "provenance.key"
    key_file.write_bytes(b"lab-fake-hmac-key-for-tests-only-32b!")
    cfg = _production_config(
        tmp_path,
        enable_strict_provenance=True,
        provenance_hmac_key_file=key_file,
    )
    cfg.validate()
    assert cfg.load_provenance_hmac_key() == b"lab-fake-hmac-key-for-tests-only-32b!"


def test_production_require_approval_token_passes(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path, require_approval_token=True)
    cfg.validate()


def test_invalid_max_request_size_fails(tmp_path: Path) -> None:
    cfg = _local_config(tmp_path)
    cfg = AppConfig(
        environment_mode=cfg.environment_mode,
        require_api_auth=cfg.require_api_auth,
        allowed_api_keys_file=cfg.allowed_api_keys_file,
        allowed_origins=cfg.allowed_origins,
        max_request_body_bytes=64,
        audit_log_dir=cfg.audit_log_dir,
        audit_retention_days=cfg.audit_retention_days,
        enable_strict_provenance=cfg.enable_strict_provenance,
        provenance_hmac_key_file=cfg.provenance_hmac_key_file,
        require_approval_token=cfg.require_approval_token,
        enable_rate_limit_guidance=cfg.enable_rate_limit_guidance,
        enable_debug_errors=cfg.enable_debug_errors,
        allow_live_external_tools=cfg.allow_live_external_tools,
        allow_shell_tools=cfg.allow_shell_tools,
        policy_path=cfg.policy_path,
        _api_keys=cfg.api_keys,
    )
    with pytest.raises(ConfigurationError, match="max_request_body_bytes"):
        cfg.validate()


def test_invalid_audit_retention_fails(tmp_path: Path) -> None:
    cfg = _local_config(tmp_path)
    cfg = AppConfig(
        environment_mode=cfg.environment_mode,
        require_api_auth=cfg.require_api_auth,
        allowed_api_keys_file=cfg.allowed_api_keys_file,
        allowed_origins=cfg.allowed_origins,
        max_request_body_bytes=cfg.max_request_body_bytes,
        audit_log_dir=cfg.audit_log_dir,
        audit_retention_days=0,
        enable_strict_provenance=cfg.enable_strict_provenance,
        provenance_hmac_key_file=cfg.provenance_hmac_key_file,
        require_approval_token=cfg.require_approval_token,
        enable_rate_limit_guidance=cfg.enable_rate_limit_guidance,
        enable_debug_errors=cfg.enable_debug_errors,
        allow_live_external_tools=cfg.allow_live_external_tools,
        allow_shell_tools=cfg.allow_shell_tools,
        policy_path=cfg.policy_path,
        _api_keys=cfg.api_keys,
    )
    with pytest.raises(ConfigurationError, match="audit_retention_days"):
        cfg.validate()


def test_config_errors_do_not_contain_api_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-live-FAKE-TEST-ONLY-do-not-use-in-production"
    keys_file = tmp_path / "keys.txt"
    keys_file.write_text(f"{secret}\n", encoding="utf-8")
    monkeypatch.setenv("ACP_ENVIRONMENT", "production")
    monkeypatch.setenv("ACP_ALLOWED_API_KEYS_FILE", str(keys_file))
    monkeypatch.setenv("ACP_ALLOWED_ORIGINS", "https://app.example.invalid")
    monkeypatch.setenv("ACP_REQUIRE_API_AUTH", "true")
    monkeypatch.delenv("ACP_API_KEY", raising=False)
    cfg = load_config_from_env()
    message = ""
    try:
        cfg.validate()
    except ConfigurationError as exc:
        message = str(exc)
    assert secret not in message


def test_production_error_detail_hides_exception_text(tmp_path: Path) -> None:
    cfg = _production_config(tmp_path)
    payload = production_error_detail(cfg, RuntimeError("sensitive-internal-detail"))
    assert payload == {"detail": "internal_error"}
    assert "sensitive" not in payload["detail"]
