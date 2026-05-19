"""Tests for enterprise integration documentation honesty (P11)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCS = _REPO_ROOT / "docs"
_README = _REPO_ROOT / "README.md"
_RELEASE_SECURITY = _DOCS / "release-security-checklist.md"

_ENTERPRISE_DOCS = (
    _DOCS / "enterprise-integration-plan.md",
    _DOCS / "identity-integration.md",
    _DOCS / "approval-workflow.md",
    _DOCS / "kms-secret-management.md",
    _DOCS / "siem-onboarding-plan.md",
    _DOCS / "rate-limiting-edge-controls.md",
    _DOCS / "enterprise-readiness-checklist.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _combined_enterprise_text() -> str:
    return "\n".join(_read(p) for p in _ENTERPRISE_DOCS)


def test_enterprise_docs_exist() -> None:
    for path in _ENTERPRISE_DOCS:
        assert path.is_file(), f"missing {path.name}"


def test_enterprise_docs_do_not_claim_idp_implemented() -> None:
    lower = _combined_enterprise_text().lower()
    forbidden = [
        "oidc is implemented",
        "saml is implemented",
        "enterprise idp is integrated",
        "idp integration is complete",
    ]
    for phrase in forbidden:
        assert phrase not in lower, f"doc must not claim: {phrase}"
    assert "not implemented" in lower or "guidance only" in lower


def test_enterprise_docs_do_not_claim_kms_implemented() -> None:
    kms = _read(_DOCS / "kms-secret-management.md").lower()
    assert "not implemented" in kms or "guidance only" in kms
    assert "kms integration is complete" not in kms


def test_enterprise_docs_do_not_claim_managed_siem_connector() -> None:
    siem = _read(_DOCS / "siem-onboarding-plan.md").lower()
    assert "managed siem connector" in siem
    assert "not implemented" in siem or "not provided" in siem
    assert "bundled siem connector is available" not in siem


def test_enterprise_docs_do_not_claim_persistent_approvals_implemented() -> None:
    approval = _read(_DOCS / "approval-workflow.md").lower()
    assert "persistent" in approval
    assert "not implemented" in approval or "in-memory" in approval
    assert "persistent approval store is deployed" not in approval


def test_enterprise_docs_do_not_claim_distributed_rate_limiting() -> None:
    rate = _read(_DOCS / "rate-limiting-edge-controls.md").lower()
    assert "distributed rate limiting is not implemented" in rate or (
        "not implemented" in rate and "rate limiting" in rate
    )
    assert "distributed rate limiting is implemented" not in rate


def test_enterprise_docs_mention_operator_responsibility() -> None:
    text = _combined_enterprise_text().lower()
    assert "operator" in text
    assert "operators must" in text or "operator-owned" in text or "operators own" in text


def test_enterprise_docs_mention_no_secrets_in_repo() -> None:
    text = _combined_enterprise_text().lower()
    assert "no secrets" in text or "no secrets in" in text


def test_readme_links_enterprise_integration_plan() -> None:
    readme = _read(_README)
    assert "enterprise-integration-plan.md" in readme


def test_release_security_checklist_mentions_enterprise_boundaries() -> None:
    text = _read(_RELEASE_SECURITY).lower()
    assert "enterprise" in text or "drop-in production" in text


def test_enterprise_plan_is_guidance_not_implementation() -> None:
    plan = _read(_DOCS / "enterprise-integration-plan.md").lower()
    assert "guidance" in plan or "planning only" in plan
    assert "drop-in production platform" in plan or "not a drop-in" in plan
