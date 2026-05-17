"""Policy integrity schema, invariants, and canonical hashing."""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

from agent_control_plane.policy_integrity import (
    PolicyIntegrityError,
    canonical_policy_json,
    compute_policy_sha256,
    load_policy_yaml,
    read_expected_hash,
    validate_policy_file,
    validate_policy_invariants,
    verify_policy_file_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = REPO_ROOT / "policies" / "default.yaml"
DEFAULT_HASH = REPO_ROOT / "policies" / "default.sha256"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate_policy.py"


def _write_policy(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "policy.yaml"
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return path


def _valid_policy_dict() -> dict[str, Any]:
    raw = yaml.safe_load(DEFAULT_POLICY.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def test_default_policy_passes_integrity() -> None:
    digest = validate_policy_file(DEFAULT_POLICY)
    assert len(digest) == 64
    verify_policy_file_hash(DEFAULT_POLICY, DEFAULT_HASH)


def test_default_hash_file_matches_computed_digest() -> None:
    raw = load_policy_yaml(DEFAULT_POLICY)
    expected = read_expected_hash(DEFAULT_HASH)
    assert compute_policy_sha256(raw) == expected


def test_canonical_hash_is_deterministic() -> None:
    raw = load_policy_yaml(DEFAULT_POLICY)
    first = compute_policy_sha256(raw)
    second = compute_policy_sha256(raw)
    assert first == second
    assert canonical_policy_json(raw) == canonical_policy_json(raw)


def test_missing_default_deny_fails(tmp_path: Path) -> None:
    path = _write_policy(
        tmp_path,
        """
        default_decision: allow
        tenant_isolation: strict
        tools:
          read_records:
            enabled: true
            risk_level: low
            external_effect: false
            destructive: false
            requires_human_approval: false
            allowed_roles: [user]
        """,
    )
    with pytest.raises(PolicyIntegrityError, match="default_decision must be 'deny'"):
        validate_policy_file(path)


def test_unknown_top_level_key_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["unexpected_section"] = {"x": 1}
    with pytest.raises(PolicyIntegrityError, match="unknown top-level keys"):
        validate_policy_invariants(raw)


def test_missing_required_tool_field_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    del raw["tools"]["read_records"]["allowed_roles"]
    with pytest.raises(PolicyIntegrityError, match="missing fields"):
        validate_policy_invariants(raw)


def test_invalid_field_type_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["read_records"]["enabled"] = "yes"
    with pytest.raises(PolicyIntegrityError, match="enabled must be a boolean"):
        validate_policy_invariants(raw)


def test_run_shell_enabled_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["run_shell"]["enabled"] = True
    raw["tools"]["run_shell"]["allowed_roles"] = ["admin"]
    with pytest.raises(PolicyIntegrityError, match="run_shell must remain disabled"):
        validate_policy_invariants(raw)


def test_send_email_without_approval_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["send_email"]["requires_human_approval"] = False
    with pytest.raises(PolicyIntegrityError, match="send_email must require human approval"):
        validate_policy_invariants(raw)


def test_export_records_without_admin_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["export_records"]["allowed_roles"] = ["user", "admin"]
    with pytest.raises(
        PolicyIntegrityError,
        match="export_records allowed_roles must be \\['admin'\\] only",
    ):
        validate_policy_invariants(raw)


def test_export_records_without_approval_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["export_records"]["requires_human_approval"] = False
    with pytest.raises(
        PolicyIntegrityError,
        match="export_records must require human approval",
    ):
        validate_policy_invariants(raw)


def test_enabled_tool_without_roles_fails(tmp_path: Path) -> None:
    raw = _valid_policy_dict()
    raw["tools"]["read_records"]["allowed_roles"] = []
    with pytest.raises(PolicyIntegrityError, match="enabled tools must declare"):
        validate_policy_invariants(raw)


def test_hash_mismatch_fails_verification(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(DEFAULT_POLICY.read_text(encoding="utf-8"), encoding="utf-8")
    hash_path = tmp_path / "policy.sha256"
    hash_path.write_text("0" * 64 + "\n", encoding="utf-8")
    with pytest.raises(PolicyIntegrityError, match="policy hash mismatch"):
        verify_policy_file_hash(policy_path, hash_path)


def _load_validate_policy_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_policy", VALIDATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_policy_script_passes_on_default_policy() -> None:
    module = _load_validate_policy_module()
    assert module.main() == 0
