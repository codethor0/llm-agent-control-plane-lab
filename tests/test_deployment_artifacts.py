"""Tests for deployment reference artifacts (P10)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

FAKE_SECRET_PATTERNS = (
    re.compile(r"sk-live-[a-zA-Z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
)

PRODUCTION_ENV = REPO_ROOT / ".env.production.example"
PRODUCTION_COMPOSE = REPO_ROOT / "docker-compose.production.yml"
K8S_DIR = REPO_ROOT / "deploy" / "kubernetes"
BOUNDARIES_DOC = REPO_ROOT / "docs" / "deployment-boundaries.md"
DEPLOY_CHECKLIST = REPO_ROOT / "docs" / "deployment-checklist.md"
FAKE_KEYS_FILE = REPO_ROOT / "deploy" / "examples" / "fake-api-keys.txt"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def test_production_env_example_has_no_real_secrets() -> None:
    content = _read(PRODUCTION_ENV)
    for pattern in FAKE_SECRET_PATTERNS:
        assert not pattern.search(content)
    assert "lab-fake" in content or "example" in content.lower()


def test_production_env_disables_live_llm_calls() -> None:
    env = _parse_env_file(PRODUCTION_ENV)
    assert env["ACP_ALLOW_LIVE_LLM_CALLS"].lower() == "false"
    assert env["ACP_LLM_ADAPTER_MODE"] == "simulated"


def test_production_env_disables_shell_tools() -> None:
    env = _parse_env_file(PRODUCTION_ENV)
    assert env["ACP_ALLOW_SHELL_TOOLS"].lower() == "false"
    assert env["ACP_ALLOW_LIVE_EXTERNAL_TOOLS"].lower() == "false"


def test_production_env_requires_api_auth() -> None:
    env = _parse_env_file(PRODUCTION_ENV)
    assert env["ACP_REQUIRE_API_AUTH"].lower() == "true"
    assert env["ACP_ENVIRONMENT"] == "production"
    assert env["ACP_ENABLE_DEBUG_ERRORS"].lower() == "false"


def test_production_compose_read_only_and_no_baked_secrets() -> None:
    data = yaml.safe_load(_read(PRODUCTION_COMPOSE))
    service = data["services"]["app"]
    assert service.get("read_only") is True
    compose_text = _read(PRODUCTION_COMPOSE)
    for pattern in FAKE_SECRET_PATTERNS:
        assert not pattern.search(compose_text)
    assert "env_file" in service
    assert ".env.production.example" in str(service["env_file"])


def test_fake_api_keys_file_is_lab_only() -> None:
    content = _read(FAKE_KEYS_FILE)
    assert "lab-fake" in content
    for pattern in FAKE_SECRET_PATTERNS:
        assert not pattern.search(content)


def test_kubernetes_secret_is_example_only() -> None:
    assert (K8S_DIR / "secret.example.yaml").is_file()
    assert not (K8S_DIR / "secret.yaml").exists()
    example = _read(K8S_DIR / "secret.example.yaml")
    assert "lab-fake" in example


def test_kubernetes_deployment_run_as_non_root() -> None:
    deployment = yaml.safe_load(_read(K8S_DIR / "deployment.yaml"))
    pod_sc = deployment["spec"]["template"]["spec"]["securityContext"]
    container_sc = deployment["spec"]["template"]["spec"]["containers"][0]["securityContext"]
    assert pod_sc.get("runAsNonRoot") is True
    assert container_sc.get("runAsNonRoot") is True
    assert container_sc.get("allowPrivilegeEscalation") is False
    caps = container_sc.get("capabilities", {})
    assert "ALL" in caps.get("drop", [])


def test_kubernetes_manifests_labeled_reference_only() -> None:
    for path in K8S_DIR.glob("*.yaml"):
        content = _read(path)
        assert "Reference only" in content or "reference only" in content


def test_deployment_boundaries_doc_honest_about_platform() -> None:
    content = _read(BOUNDARIES_DOC).lower()
    assert "not a drop-in production" in content or "not a drop-in production platform" in content
    assert "operator must provide" in content


def test_deployment_checklist_does_not_claim_production_ready() -> None:
    content = _read(DEPLOY_CHECKLIST).lower()
    assert "reference implementation" in content or "not a managed production" in content
    assert "organizational" in content or "operator" in content
