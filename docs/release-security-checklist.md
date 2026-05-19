# Release Security Checklist

Use before tagging a release (for example `v0.2.x`). Complements [release-checklist.md](release-checklist.md) with supply-chain and CI gates.

**Honest scope:** Passing this checklist improves release hygiene. It does **not** certify production readiness or guarantee absence of vulnerabilities.

## Pre-release validation (host)

Requires Python 3.12.

```bash
make setup
make validate
make demo
python scripts/validate_repo.py
python scripts/validate_policy.py
```

Expected:

- pytest: **271 passed** (host and Docker via `make validate`; 260 on v0.2.6)
- `make demo`: 7 scenarios OK
- repo hygiene: no prompt artifacts
- policy integrity: canonical SHA-256 matches `policies/default.sha256`
- bandit / pip-audit: pass (network required for pip-audit)

## GitHub Actions (must be green on release commit)

Confirm on `main` (or release branch) via [Actions](https://github.com/codethor0/llm-agent-control-plane/actions):

| Workflow | Purpose |
|----------|---------|
| CI | Lint, types, tests, bandit, pip-audit, Docker pytest |
| CodeQL | Static analysis (Python) |
| Secret scan | Gitleaks (repository history) |
| Trivy | Container image CRITICAL/HIGH (unfixed) |
| SBOM | CycloneDX artifact upload |

Do not tag if required workflows are failing or skipped without documented reason.

## Supply-chain artifacts

- [ ] Download SBOM artifact from latest green `SBOM` workflow run (`sbom-cyclonedx`)
- [ ] SBOM is **not signed** unless signing is explicitly implemented and documented
- [ ] Review Trivy results for new CRITICAL/HIGH issues on the release image
- [ ] Review CodeQL alerts (if any) for the release commit

## Repo hygiene and secrets

- [ ] No `.env`, credentials, or real API keys in the tree
- [ ] `python scripts/validate_repo.py` passes
- [ ] Gitleaks workflow green (tests/ allowlist is tests-only per `.gitleaks.toml`)
- [ ] No prompt artifacts, cycle reports, or chat exports committed

## Policy and runtime claims

- [ ] `python scripts/validate_policy.py` passes
- [ ] Release notes state scope: defensive lab, simulated tools only
- [ ] No unsupported claims ("production-ready", "unhackable", exhaustive fuzzing)
- [ ] Property-based tests described as bounded coverage, not proof of absence of bugs

## Tag and GitHub release

- [ ] Tag points at intended commit on `main` (`git show vX.Y.Z`)
- [ ] Annotated tag message matches release title
- [ ] `gh release create` uses `docs/github-release-notes-vX.Y.Z.md`
- [ ] Prior release tags unchanged (no history rewrite)
- [ ] README "Latest release" updated if publishing a new latest version

## Post-release

- [ ] Verify release page and tag on GitHub
- [ ] Monitor Dependabot PRs for critical dependency updates
- [ ] File issues for accepted CodeQL/Trivy findings with mitigation plan

## Production deployment (P7)

- [ ] `ACP_ENVIRONMENT=production` validation passes at startup
- [ ] API auth and CORS configured per [production-hardening.md](production-hardening.md)
- [ ] Container runs non-root; read-only rootfs where applicable
- [ ] No claim of production certification in release notes

## Related docs

- [branch-protection.md](branch-protection.md) — recommended `main` protection (guidance only until configured)
- [supply-chain.md](supply-chain.md) — workflows, pinning policy, limitations
- [production-hardening.md](production-hardening.md) — deployment profile
- [release-checklist.md](release-checklist.md) — general publication checklist
