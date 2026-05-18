# Supply Chain Security (P6)

Supply-chain workflows and configuration added in P6 improve **open-source release hygiene** and CI verification. They do **not** guarantee supply-chain security or production certification.

## Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| CI | `.github/workflows/ci.yml` | push/PR `main` | Lint, types, 210 tests, bandit, pip-audit, Docker |
| CodeQL | `.github/workflows/codeql.yml` | push/PR `main`, weekly | Python static analysis (GitHub CodeQL) |
| Secret scan | `.github/workflows/secrets.yml` | push/PR `main` | Gitleaks on full git history |
| Trivy | `.github/workflows/trivy.yml` | push/PR `main` | CRITICAL/HIGH on built Docker image |
| SBOM | `.github/workflows/sbom.yml` | push/PR `main`, manual | CycloneDX JSON artifact (unsigned) |

## Dependabot

`.github/dependabot.yml` opens weekly update PRs for:

- GitHub Actions (limit 5 open)
- pip dependencies (limit 5 open, dev group for test/lint tools)

No private registry or repository secrets required.

## GitHub Actions pinning policy

- **First-party actions:** pin to major version tags (`actions/checkout@v4`, `actions/upload-artifact@v4`, `github/codeql-action/*@v3`).
- **Third-party actions:** pin to explicit release tags where used:
  - `gitleaks/gitleaks-action@v2` — secret scanning without custom credentials
  - `aquasecurity/trivy-action@0.36.0` — container CVE scan
  - `anchore/sbom-action@v0` — SBOM generation (Syft-based)
- Full commit SHA pinning is optional hardening; Dependabot can propose Action updates.
- Do not add untrusted third-party actions without documenting rationale here.

## Gitleaks allowlist

`.gitleaks.toml` extends default rules and allowlists **`tests/` only** for lab-labeled fake secret strings used in output-filter and audit redaction tests (`FAKE-TEST-ONLY`, `lab-fake-*`). `src/` and `policies/` are not allowlisted.

## SBOM artifact

On a green `SBOM` workflow run, download artifact **`sbom-cyclonedx`** from the Actions run. Format: CycloneDX JSON (`sbom.cyclonedx.json`). **Not signed** unless a future release adds signing.

## Trivy policy

- Builds `llm-agent-control-plane:scan` from the repo `Dockerfile` (no registry push).
- Fails on **CRITICAL** and **HIGH** with `ignore-unfixed: true`.
- Does not replace ongoing base-image maintenance.

## Signed tags and releases

Signed annotated tags and GitHub release signing are **recommended** for maintainers but **not automated** in this repository. See [release-security-checklist.md](release-security-checklist.md).

## Branch protection

Recommended settings are documented in [branch-protection.md](branch-protection.md). Enabling them is a repository administrator action outside this codebase.

## Limitations

- Scans are point-in-time; new CVEs may appear after a green run.
- Gitleaks cannot detect all secret types; allowlist scope must stay minimal.
- CodeQL and Trivy may report false positives; triage in GitHub Security tab.
- SBOM lists components at generation time; it is not a vulnerability scan by itself.
- Dependabot PRs require human review before merge.

## Local validation

Supply-chain workflows run in GitHub Actions. Local release validation:

```bash
make validate
make demo
python scripts/validate_repo.py
python scripts/validate_policy.py
```

Optional: install [gitleaks](https://github.com/gitleaks/gitleaks) and run `gitleaks detect --config .gitleaks.toml` locally before pushing.
