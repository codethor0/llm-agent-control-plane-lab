"""Tests for release provenance documentation and release-artifacts workflow safety."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCS = _REPO_ROOT / "docs"
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"
_RELEASE_WORKFLOW = _WORKFLOWS / "release-artifacts.yml"

_PROVENANCE_DOC = _DOCS / "release-provenance.md"
_VERIFICATION_DOC = _DOCS / "artifact-verification.md"
_RELEASE_SECURITY_CHECKLIST = _DOCS / "release-security-checklist.md"
_RELEASE_CHECKLIST = _DOCS / "release-checklist.md"
_README = _REPO_ROOT / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture
def provenance_text() -> str:
    return _read(_PROVENANCE_DOC)


@pytest.fixture
def verification_text() -> str:
    return _read(_VERIFICATION_DOC)


@pytest.fixture
def release_workflow_text() -> str:
    assert _RELEASE_WORKFLOW.is_file(), "release-artifacts workflow must exist"
    return _read(_RELEASE_WORKFLOW)


def test_release_provenance_doc_exists(provenance_text: str) -> None:
    assert "not yet signed" in provenance_text.lower() or "not signed" in provenance_text.lower()
    assert "slsa" in provenance_text.lower()
    assert "do not claim" in provenance_text.lower() or "not claim" in provenance_text.lower()


def test_release_provenance_does_not_claim_signed_releases(provenance_text: str) -> None:
    lower = provenance_text.lower()
    forbidden = [
        "releases are cryptographically signed",
        "all releases are signed",
        "cosign-signed releases are available",
        "slsa level 3",
    ]
    for phrase in forbidden:
        assert phrase not in lower, f"doc must not claim: {phrase}"


def test_artifact_verification_mentions_unsigned_limitations(verification_text: str) -> None:
    lower = verification_text.lower()
    assert "unsigned" in lower or "not signed" in lower
    assert "cannot be verified" in lower or "what cannot be verified" in lower


def test_release_workflow_triggers_on_version_tags(release_workflow_text: str) -> None:
    assert "tags:" in release_workflow_text
    assert '"v*"' in release_workflow_text or "'v*'" in release_workflow_text


def test_release_workflow_generates_sha256sums(release_workflow_text: str) -> None:
    assert "SHA256SUMS" in release_workflow_text
    assert "sha256sum" in release_workflow_text
    assert "git archive" in release_workflow_text


def test_release_workflow_no_custom_secrets(release_workflow_text: str) -> None:
    secret_refs = re.findall(r"secrets\.[A-Za-z0-9_]+", release_workflow_text)
    assert secret_refs == [], f"unexpected custom secrets: {secret_refs}"
    assert "github.token" in release_workflow_text


def test_release_workflow_does_not_push_images_or_publish_credentials(
    release_workflow_text: str,
) -> None:
    lower = release_workflow_text.lower()
    assert "docker push" not in lower
    assert "registry" not in lower or "no registry" in _read(_DOCS / "supply-chain.md").lower()
    forbidden = ["aws_secret", "api_key", "password:", "credentials.json"]
    for token in forbidden:
        assert token not in lower


def test_release_security_checklist_includes_provenance_gates() -> None:
    text = _read(_RELEASE_SECURITY_CHECKLIST).lower()
    assert "tag" in text
    assert "ci" in text or "github actions" in text
    assert "sbom" in text
    assert "prompt artifact" in text or "prompt artifacts" in text
    assert "sha256" in text or "checksum" in text
    assert "sign" in text


def test_release_checklist_links_provenance_docs() -> None:
    text = _read(_RELEASE_CHECKLIST)
    assert "release-provenance.md" in text or "artifact-verification.md" in text


def test_readme_links_release_provenance_docs() -> None:
    text = _read(_README)
    assert "release-provenance.md" in text
    assert "artifact-verification.md" in text


def test_github_actions_trust_doc_lists_workflows() -> None:
    text = _read(_DOCS / "github-actions-trust.md")
    assert "release-artifacts.yml" in text
    assert "ci.yml" in text
    assert "pin" in text.lower()
