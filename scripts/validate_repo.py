#!/usr/bin/env python3
"""Scan the repository for forbidden prompt artifacts and AI conversation exports."""

from __future__ import annotations

import sys
from pathlib import Path

ALLOWED_GOVERNANCE_FILES: frozenset[str] = frozenset(
    {
        "PROJECT_DOCTRINE.md",
        "AGENTS.md",
        ".cursor/rules/project-doctrine.mdc",
        ".cursor/rules/security-controls.mdc",
        ".cursor/rules/testing.mdc",
    }
)

SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "audit_logs",
        "htmlcov",
        "dist",
        "build",
        ".eggs",
    }
)

FORBIDDEN_DIR_NAMES: frozenset[str] = frozenset(
    {
        "master-prompts",
        "prompts",
        "prompt-artifacts",
        "chat-logs",
        "cursor-transcripts",
        "conversation-exports",
        "agent-reports",
        "scratchpads",
        "validation-notes",
        "ai-notes",
    }
)

FORBIDDEN_PATH_SUBSTRINGS: tuple[str, ...] = (
    "master-prompts",
    "prompt-artifacts",
    "cursor-transcripts",
    "conversation-exports",
    "chat-logs",
    "agent-reports",
    "scratchpads",
    "validation-notes",
    "ai-notes",
    "cycle-report",
)

FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".prompt.md",
    ".prompts.md",
    ".chat.md",
    ".transcript.md",
)

FORBIDDEN_NAME_FRAGMENTS: tuple[str, ...] = (
    "cursor_project_doctrine",
    "cycle-report",
    "llm-agent-control-plane-lab-cycle-report.md",
)


def find_repo_root(start: Path | None = None) -> Path:
    """Locate repository root by pyproject.toml."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return current


def is_skipped_dir(path: Path) -> bool:
    """Return True if any path component is a skipped cache or environment directory."""
    return any(part in SKIP_DIR_NAMES or part.startswith("pytest-of-") for part in path.parts)


def is_allowed_governance_file(relative_path: str) -> bool:
    """Return True for committed governance files that may mention prompts in doctrine."""
    return relative_path in ALLOWED_GOVERNANCE_FILES


def check_file(relative_path: str) -> str | None:
    """
    Return a violation message if the file is a forbidden prompt artifact.

    Invariant: only governance doctrine files may reference prompt policy; working prompts
    and AI transcripts must never be committed.
    """
    if is_allowed_governance_file(relative_path):
        return None

    if relative_path.startswith(".cursor/rules/") and relative_path.endswith(".mdc"):
        return f"non-doctrine Cursor rule file not allowed: {relative_path}"

    path_obj = Path(relative_path)
    parts = path_obj.parts
    name_lower = path_obj.name.lower()
    rel_lower = relative_path.replace("\\", "/").lower()

    for part in parts:
        if part in FORBIDDEN_DIR_NAMES:
            return f"forbidden directory segment '{part}': {relative_path}"

    for fragment in FORBIDDEN_PATH_SUBSTRINGS:
        if fragment in rel_lower:
            return f"forbidden path fragment '{fragment}': {relative_path}"

    for suffix in FORBIDDEN_SUFFIXES:
        if name_lower.endswith(suffix):
            return f"forbidden filename suffix '{suffix}': {relative_path}"

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        if fragment in name_lower:
            return f"forbidden filename fragment '{fragment}': {relative_path}"

    return None


def scan_repository(root: Path) -> list[str]:
    """Walk the repository and collect prompt artifact hygiene violations."""
    violations: list[str] = []
    root = root.resolve()

    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if is_skipped_dir(path.relative_to(root)):
            continue

        relative = path.relative_to(root).as_posix()
        message = check_file(relative)
        if message is not None:
            violations.append(message)

    return sorted(violations)


def main() -> int:
    """Run repository hygiene scan; exit 1 if violations are found."""
    root = find_repo_root()
    violations = scan_repository(root)
    if not violations:
        print(f"OK: no prompt artifacts found under {root}")
        return 0

    print("ERROR: prompt artifact hygiene violations detected:", file=sys.stderr)
    for item in violations:
        print(f"  - {item}", file=sys.stderr)
    print(
        "Only governance files may discuss prompt policy: "
        "PROJECT_DOCTRINE.md, AGENTS.md, .cursor/rules/*.mdc (doctrine rules only).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
