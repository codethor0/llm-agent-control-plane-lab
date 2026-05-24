"""Property-based tests for repository prompt-artifact hygiene."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VALIDATE_REPO_PATH = _REPO_ROOT / "scripts" / "validate_repo.py"


def _load_validate_repo() -> object:
    spec = importlib.util.spec_from_file_location("validate_repo", _VALIDATE_REPO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_VALIDATE_REPO = _load_validate_repo()
check_file = _VALIDATE_REPO.check_file  # type: ignore[attr-defined]
scan_repository = _VALIDATE_REPO.scan_repository  # type: ignore[attr-defined]
FORBIDDEN_GOVERNANCE = _VALIDATE_REPO.FORBIDDEN_EXACT_FILES  # type: ignore[attr-defined]


@given(st.sampled_from(sorted(FORBIDDEN_GOVERNANCE)))
def test_property_forbidden_governance_files_fail(relative_path: str) -> None:
    message = check_file(relative_path)
    assert message is not None


@given(
    st.sampled_from(
        [
            "master-prompts",
            "prompt-artifacts",
            "cursor-transcripts",
            "cycle-report",
        ]
    ),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=12),
)
def test_property_forbidden_path_fragments_fail(fragment: str, name: str) -> None:
    relative = f"docs/{fragment}-{name}.md"
    message = check_file(relative)
    assert message is not None


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=16))
def test_property_benign_doc_names_pass(name: str) -> None:
    assume("prompt" not in name)
    assume("cycle-report" not in name)
    assume("transcript" not in name)
    relative = f"docs/{name}.md"
    assert check_file(relative) is None


def test_property_cursor_directory_fails(tmp_path: Path) -> None:
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "custom-rule.mdc").write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")
    violations = scan_repository(tmp_path)
    assert any(".cursor" in item for item in violations)


def test_property_ignored_cache_dirs_skipped(tmp_path: Path) -> None:
    cache = tmp_path / ".pytest_cache" / "v"
    cache.mkdir(parents=True)
    (cache / "README").write_text("cache", encoding="utf-8")
    assert scan_repository(tmp_path) == []
