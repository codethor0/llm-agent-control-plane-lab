"""Tests for prompt artifact repository hygiene scanning."""

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VALIDATE_REPO_PATH = _REPO_ROOT / "scripts" / "validate_repo.py"


def _load_validate_repo() -> object:
    spec = importlib.util.spec_from_file_location("validate_repo", _VALIDATE_REPO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validate_repo() -> object:
    return _load_validate_repo()


def test_allowed_governance_files_pass(validate_repo: object) -> None:
    for rel in validate_repo.ALLOWED_GOVERNANCE_FILES:  # type: ignore[attr-defined]
        assert validate_repo.check_file(rel) is None  # type: ignore[attr-defined]


def test_prompt_artifact_directory_fails(validate_repo: object, tmp_path: Path) -> None:
    bad_dir = tmp_path / "master-prompts"
    bad_dir.mkdir()
    (bad_dir / "build.prompt.md").write_text("secret prompt", encoding="utf-8")
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert violations
    assert any("master-prompts" in item for item in violations)


def test_prompt_artifact_filename_suffix_fails(validate_repo: object, tmp_path: Path) -> None:
    (tmp_path / "notes.prompt.md").write_text("do not commit", encoding="utf-8")
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert any("forbidden filename suffix" in item for item in violations)


def test_cursor_rules_mdc_allowed_under_cursor_rules(validate_repo: object, tmp_path: Path) -> None:
    rules_dir = tmp_path / ".cursor" / "rules"
    rules_dir.mkdir(parents=True)
    allowed = rules_dir / "project-doctrine.mdc"
    allowed.write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")

    assert validate_repo.check_file(".cursor/rules/project-doctrine.mdc") is None  # type: ignore[attr-defined]
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert violations == []


def test_non_doctrine_cursor_rule_file_fails(validate_repo: object, tmp_path: Path) -> None:
    rules_dir = tmp_path / ".cursor" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "chat-export.mdc").write_text("transcript content", encoding="utf-8")
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert violations


def test_ignored_cache_paths_do_not_fail(validate_repo: object, tmp_path: Path) -> None:
    cache_dir = tmp_path / ".venv" / "master-prompts"
    cache_dir.mkdir(parents=True)
    (cache_dir / "hidden.prompt.md").write_text("ignored", encoding="utf-8")
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert violations == []


def test_ignored_pytest_basetemp_paths_do_not_fail(validate_repo: object, tmp_path: Path) -> None:
    basetemp = tmp_path / "pytest-of-user" / "pytest-0" / "test_prompt_artifact_directory0"
    bad_dir = basetemp / "master-prompts"
    bad_dir.mkdir(parents=True)
    (bad_dir / "build.prompt.md").write_text("test fixture", encoding="utf-8")
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert violations == []


def test_repository_root_passes_hygiene_scan(validate_repo: object) -> None:
    violations = validate_repo.scan_repository(_REPO_ROOT)  # type: ignore[attr-defined]
    assert violations == []


def test_cycle_report_filename_fails(validate_repo: object, tmp_path: Path) -> None:
    (tmp_path / "llm-agent-control-plane-cycle-report.md").write_text(
        "cycle notes",
        encoding="utf-8",
    )
    violations = validate_repo.scan_repository(tmp_path)  # type: ignore[attr-defined]
    assert any("cycle-report" in item for item in violations)
