"""Policy file schema validation and canonical integrity hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from agent_control_plane.models import RiskLevel

ALLOWED_TOP_LEVEL_KEYS = frozenset({"default_decision", "tools", "tenant_isolation"})
REQUIRED_TOOL_KEYS = frozenset(
    {
        "enabled",
        "risk_level",
        "external_effect",
        "destructive",
        "requires_human_approval",
        "allowed_roles",
    }
)
REQUIRED_DEMO_TOOLS = frozenset(
    {
        "read_records",
        "send_email",
        "export_records",
        "delete_records",
        "run_shell",
    }
)
BOOL_KEYS = frozenset({"enabled", "external_effect", "destructive", "requires_human_approval"})
VALID_RISK_LEVELS = frozenset(level.value for level in RiskLevel)


class PolicyIntegrityError(ValueError):
    """Policy file failed schema or invariant checks."""


def load_policy_yaml(path: Path) -> dict[str, Any]:
    """Load policy YAML as a mapping; raises PolicyIntegrityError on invalid input."""
    if not path.is_file():
        raise PolicyIntegrityError(f"policy file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PolicyIntegrityError("policy root must be a mapping")
    return raw


def canonical_policy_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic JSON-serializable policy structure."""
    tools_raw = raw.get("tools")
    if not isinstance(tools_raw, dict):
        raise PolicyIntegrityError("tools must be a mapping")

    canonical_tools: dict[str, dict[str, Any]] = {}
    for name in sorted(tools_raw.keys()):
        cfg = tools_raw[name]
        if not isinstance(cfg, dict):
            raise PolicyIntegrityError(f"tool {name!r} must be a mapping")
        canonical_tools[name] = {
            key: _canonical_tool_value(key, cfg[key]) for key in sorted(cfg.keys())
        }

    return {
        "default_decision": raw.get("default_decision"),
        "tenant_isolation": raw.get("tenant_isolation"),
        "tools": canonical_tools,
    }


def _canonical_tool_value(key: str, value: Any) -> Any:
    if key == "allowed_roles":
        if not isinstance(value, list):
            raise PolicyIntegrityError("allowed_roles must be a list")
        roles = [str(item) for item in value]
        return sorted(roles)
    if key in BOOL_KEYS:
        if not isinstance(value, bool):
            raise PolicyIntegrityError(f"{key} must be a boolean")
        return value
    if key == "risk_level":
        return str(value)
    return value


def canonical_policy_json(raw: dict[str, Any]) -> str:
    """Serialize policy to canonical JSON (sorted keys, stable tool order)."""
    payload = canonical_policy_payload(raw)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_policy_sha256(raw: dict[str, Any]) -> str:
    """Return lowercase hex SHA-256 of canonical policy JSON."""
    digest = hashlib.sha256(canonical_policy_json(raw).encode("utf-8")).hexdigest()
    return digest


def read_expected_hash(path: Path) -> str:
    """Read expected SHA-256 hex from a hash file (first non-empty, non-comment line)."""
    if not path.is_file():
        raise PolicyIntegrityError(f"expected hash file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        token = stripped.split()[0].lower()
        if len(token) != 64 or any(c not in "0123456789abcdef" for c in token):
            raise PolicyIntegrityError(f"invalid hash in {path}: {stripped!r}")
        return token
    raise PolicyIntegrityError(f"no hash found in {path}")


def validate_policy_invariants(raw: dict[str, Any]) -> None:
    """Validate policy schema and lab security invariants."""
    unknown_top = set(raw.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_top:
        raise PolicyIntegrityError(f"unknown top-level keys: {', '.join(sorted(unknown_top))}")

    default_decision = raw.get("default_decision")
    if default_decision != "deny":
        raise PolicyIntegrityError("default_decision must be 'deny'")

    tenant_isolation = raw.get("tenant_isolation")
    if tenant_isolation != "strict":
        raise PolicyIntegrityError("tenant_isolation must be 'strict'")

    tools_raw = raw.get("tools")
    if not isinstance(tools_raw, dict):
        raise PolicyIntegrityError("tools must be a mapping")
    if not tools_raw:
        raise PolicyIntegrityError("tools mapping must not be empty")

    missing_tools = REQUIRED_DEMO_TOOLS - set(tools_raw.keys())
    if missing_tools:
        raise PolicyIntegrityError(
            f"missing required demo tools: {', '.join(sorted(missing_tools))}"
        )

    for name, cfg in tools_raw.items():
        if not isinstance(name, str):
            raise PolicyIntegrityError("tool names must be strings")
        if not isinstance(cfg, dict):
            raise PolicyIntegrityError(f"tool {name!r} must be a mapping")
        unknown_tool_keys = set(cfg.keys()) - REQUIRED_TOOL_KEYS
        if unknown_tool_keys:
            raise PolicyIntegrityError(
                f"tool {name!r} has unknown keys: {', '.join(sorted(unknown_tool_keys))}"
            )
        missing_fields = REQUIRED_TOOL_KEYS - set(cfg.keys())
        if missing_fields:
            raise PolicyIntegrityError(
                f"tool {name!r} missing fields: {', '.join(sorted(missing_fields))}"
            )
        _validate_tool_field_types(name, cfg)
        _validate_tool_security_invariants(name, cfg)


def _validate_tool_field_types(name: str, cfg: dict[str, Any]) -> None:
    for key in BOOL_KEYS:
        if not isinstance(cfg[key], bool):
            raise PolicyIntegrityError(f"tool {name!r}: {key} must be a boolean")
    if not isinstance(cfg["allowed_roles"], list):
        raise PolicyIntegrityError(f"tool {name!r}: allowed_roles must be a list")
    if not all(isinstance(role, str) for role in cfg["allowed_roles"]):
        raise PolicyIntegrityError(f"tool {name!r}: allowed_roles entries must be strings")
    risk = cfg["risk_level"]
    if not isinstance(risk, str) or risk not in VALID_RISK_LEVELS:
        raise PolicyIntegrityError(
            f"tool {name!r}: risk_level must be one of {sorted(VALID_RISK_LEVELS)}"
        )


def _validate_tool_security_invariants(name: str, cfg: dict[str, Any]) -> None:
    enabled = cfg["enabled"]
    roles: list[str] = cfg["allowed_roles"]
    if enabled and not roles:
        raise PolicyIntegrityError(
            f"tool {name!r}: enabled tools must declare at least one allowed role"
        )

    if name == "run_shell" and enabled:
        raise PolicyIntegrityError("run_shell must remain disabled (enabled: false)")

    if name == "send_email" and not cfg["requires_human_approval"]:
        raise PolicyIntegrityError("send_email must require human approval")

    if name == "export_records":
        if not cfg["requires_human_approval"]:
            raise PolicyIntegrityError("export_records must require human approval")
        if roles != ["admin"]:
            raise PolicyIntegrityError("export_records allowed_roles must be ['admin'] only")


def validate_policy_file(path: Path) -> str:
    """
    Load, validate invariants, and return canonical SHA-256 hex digest.

    Raises PolicyIntegrityError on failure.
    """
    raw = load_policy_yaml(path)
    validate_policy_invariants(raw)
    return compute_policy_sha256(raw)


def verify_policy_file_hash(
    policy_path: Path,
    hash_path: Path,
) -> str:
    """Validate policy and ensure digest matches the checked-in hash file."""
    actual = validate_policy_file(policy_path)
    expected = read_expected_hash(hash_path)
    if actual != expected:
        raise PolicyIntegrityError(f"policy hash mismatch: expected {expected}, got {actual}")
    return actual
