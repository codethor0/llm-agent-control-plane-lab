# GitHub Actions Trust

This document inventories **GitHub Actions** used in **llm-agent-control-plane**, explains pinning choices, and records maintenance expectations. It supports [release-provenance.md](release-provenance.md) and [supply-chain.md](supply-chain.md).

**Not claimed:** SLSA compliance, immutable action supply chain, or signed workflow attestations.

## Workflows inventory

| Workflow | File | Trigger | Primary actions |
|----------|------|---------|-----------------|
| CI | `ci.yml` | push/PR `main` | `actions/checkout@v4`, `actions/setup-python@v5` |
| CodeQL | `codeql.yml` | push/PR `main`, weekly | `actions/checkout@v4`, `github/codeql-action/*@v3` |
| Secret scan | `secrets.yml` | push/PR `main` | `actions/checkout@v4`, `gitleaks/gitleaks-action@v2` |
| Trivy | `trivy.yml` | push/PR `main` | `actions/checkout@v4`, `aquasecurity/trivy-action@v0.36.0` |
| SBOM | `sbom.yml` | push/PR `main`, manual | `actions/checkout@v4`, `anchore/sbom-action@v0`, `actions/upload-artifact@v4` |
| Release artifacts | `release-artifacts.yml` | push tag `v*` | `actions/checkout@v4`, `actions/upload-artifact@v4`, `gh` CLI (runner built-in) |

## Pinning strategy

### Major-version pins (current default)

First-party and many third-party actions use **moving major tags** (for example `@v4`, `@v3`, `@v2`):

- **Benefit:** Dependabot can propose security updates with readable release notes.
- **Risk:** Tag retag or compromise of the action publisher could change behavior without a repo commit.

### Exact third-party version pins

Where used today:

- `aquasecurity/trivy-action@v0.36.0` — container scan behavior tied to a known release.

### Full commit SHA pins (future option)

Pinning `uses: owner/repo@<40-char-sha>` is the strongest pin against tag movement. Tradeoffs:

- Every security fix requires a deliberate SHA bump in this repository.
- Dependabot still helps but diffs are noisier.
- All workflows must be re-validated after each bump (`make validate` locally; CI on PR).

**Project decision (P12):** Do not mass-migrate to SHA pins in this change set. Document the process first; migrate in a focused follow-up with full CI validation.

## Secrets and permissions

| Workflow | `permissions` | Secrets |
|----------|---------------|---------|
| CI, CodeQL, Secret scan, Trivy, SBOM | `contents: read` (CodeQL adds `security-events: write`) | Gitleaks uses `GITHUB_TOKEN` only |
| Release artifacts | `contents: write` (release upload only) | `GITHUB_TOKEN` via `github.token` / `gh` CLI only |

No workflow should reference:

- `secrets.*` custom repository secrets (none required today)
- Registry credentials or cloud API keys
- `docker push` or image publication

## Operational maintenance

1. **Dependabot** (`.github/dependabot.yml`) — review Actions and pip PRs; run full CI before merge.
2. **New actions** — add a row to this file and [supply-chain.md](supply-chain.md) with rationale; prefer established publishers.
3. **Tag releases** — only after green CI on the intended commit; see [release-security-checklist.md](release-security-checklist.md).
4. **Release artifacts** — created automatically on `v*` tag push; verify assets on the Release page after publish.

## Known limitations

- Moving `@v4` tags trust GitHub and action maintainers.
- `GITHUB_TOKEN` scoped to the repository cannot protect against a malicious commit merged to `main`.
- Workflow definitions are not signed; reviewers must read YAML in PRs.
- Fork PRs from untrusted contributors run with restricted tokens; do not merge without review.

## Related documentation

- [supply-chain.md](supply-chain.md)
- [release-provenance.md](release-provenance.md)
- [artifact-verification.md](artifact-verification.md)
