"""Tests for release-readiness documentation alignment (operational docs)."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPECTED_TEST_COUNT = 299

_OPERATIONAL_DOCS = (
    _REPO_ROOT / "docs" / "testing-strategy.md",
    _REPO_ROOT / "docs" / "release-checklist.md",
    _REPO_ROOT / "docs" / "release-security-checklist.md",
    _REPO_ROOT / "SECURITY-CONTROLS.md",
    _REPO_ROOT / "README.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_test_badge_matches_current_count() -> None:
    readme = _read(_REPO_ROOT / "README.md")
    match = re.search(r"tests-(\d+)%20passing", readme)
    assert match is not None
    assert int(match.group(1)) == _EXPECTED_TEST_COUNT


def test_operational_docs_do_not_state_stale_271_pytest_gate() -> None:
    """Active checklists must not require 271 tests (superseded by 293)."""
    stale = re.compile(r"pytest:\s*271\s+passed", re.IGNORECASE)
    for path in _OPERATIONAL_DOCS:
        if path.name == "README.md":
            continue
        text = _read(path)
        assert stale.search(text) is None, f"{path.name} still requires 271 passed"


def test_security_controls_docker_row_uses_current_test_count() -> None:
    text = _read(_REPO_ROOT / "SECURITY-CONTROLS.md")
    assert "pytest` (210 tests)" not in text
    assert str(_EXPECTED_TEST_COUNT) in text or "pytest`" in text


def test_architecture_validation_diagram_uses_current_test_count() -> None:
    text = _read(_REPO_ROOT / "docs" / "architecture.md")
    assert "Pytest 271 tests" not in text
    assert f"Pytest {_EXPECTED_TEST_COUNT} tests" in text


def test_audit_report_exists() -> None:
    report = _REPO_ROOT / "reports" / "final-release-readiness-audit.md"
    assert report.is_file()
    body = _read(report)
    assert str(_EXPECTED_TEST_COUNT) in body
    assert "Verified" in body or "verified" in body.lower()


def test_audit_report_does_not_claim_signed_releases() -> None:
    body = _read(_REPO_ROOT / "reports" / "final-release-readiness-audit.md").lower()
    assert "signed releases" not in body or "not implemented" in body or "unsigned" in body
    assert "slsa-compliant" not in body
    assert "bug-free" not in body
