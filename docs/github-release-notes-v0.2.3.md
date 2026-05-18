## Summary

**v0.2.3** adds supply-chain security workflows and release hygiene documentation. No runtime behavior changes in `src/agent_control_plane/`.

This remains a **production-oriented defensive reference implementation**, not a drop-in production service.

## What changed since v0.2.2

| Area | Change |
|------|--------|
| CodeQL | Python static analysis on push/PR and weekly schedule |
| Dependabot | Weekly pip and GitHub Actions update PRs |
| Gitleaks | Secret scan on full git history |
| Trivy | Container image scan (CRITICAL/HIGH, unfixed) |
| SBOM | CycloneDX JSON artifact per workflow run (unsigned) |
| Docker | Debian security upgrades during image build |
| Docs | Supply-chain, branch protection, release security checklists |

## P6: Supply-chain hardening

| Control | Implementation |
|---------|----------------|
| CodeQL | `.github/workflows/codeql.yml` |
| Dependabot | `.github/dependabot.yml` |
| Secret scan | `.github/workflows/secrets.yml`, `.gitleaks.toml` (`tests/` allowlist only) |
| Trivy | `.github/workflows/trivy.yml` |
| SBOM | `.github/workflows/sbom.yml` |
| Guidance | `docs/supply-chain.md`, `docs/branch-protection.md`, `docs/release-security-checklist.md` |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 210 passed |
| docker compose pytest | 210 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- No changes to `src/agent_control_plane/` application logic
- Simulated tools only; no live LLM API
- v0.2.2 and earlier release tags unchanged

## Honest limitations

- Supply-chain workflows improve **release hygiene**; they do **not guarantee** supply-chain security
- SBOM is **unsigned** unless signing is added in a future release
- [branch-protection.md](branch-protection.md) is **guidance only** until configured in GitHub Settings
- Trivy results are **point-in-time**; new CVEs may appear after a green run
- Gitleaks allowlist is narrow (`tests/` only) but does **not replace** secret hygiene in other paths
- Dependabot PRs require maintainer review

## Prior releases

- [v0.2.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.2) — property-based security coverage
- [v0.2.1](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.1) — layered output filtering
- [v0.2.0](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.0) — integrity hardening (P0-P3)

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
