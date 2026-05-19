## Summary

**v0.2.8** completes **P12: release provenance and checksums**. This release adds documentation for release trust, a tag-triggered workflow that publishes unsigned `SHA256SUMS` and a source tarball, artifact verification guidance, and GitHub Actions trust inventory.

This remains a **production-oriented defensive reference implementation**, not a managed production platform.

## What changed since v0.2.7

| Area | Change |
|------|--------|
| Workflow | `.github/workflows/release-artifacts.yml` — `git archive` + SHA256SUMS on `v*` tag push |
| Docs | [release-provenance.md](release-provenance.md), [artifact-verification.md](artifact-verification.md), [github-actions-trust.md](github-actions-trust.md) |
| Checklists | [release-checklist.md](release-checklist.md), [release-security-checklist.md](release-security-checklist.md), [supply-chain.md](supply-chain.md) |
| Tests | **282** pytest tests (was 271 on v0.2.7) |

## P12: Release provenance and checksums

| Control | Implementation |
|---------|----------------|
| Release trust docs | Verified vs unsigned; honest limitations |
| SHA256SUMS | Generated on tag push; attached to GitHub Release |
| Source tarball | `llm-agent-control-plane-<tag>.tar.gz` from `git archive` |
| Verification guide | Tag, CI, SBOM, checksum steps for consumers |
| Actions trust | Pinning inventory and maintenance notes |
| False-claim tests | `tests/test_release_artifacts.py` blocks signing overclaims |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 282 passed |
| docker compose pytest | 282 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- **No runtime control-plane behavior changes** in `src/agent_control_plane/`
- Simulated tools only; **no live external tool execution**
- **No live LLM API calls**
- **No secrets** added to the repository
- v0.2.7 and earlier release tags unchanged

## Honest limitations

- **Checksums are unsigned** — SHA256 proves file integrity after download, not publisher identity
- **No cosign**, **no GPG-signed tags**, **no SLSA compliance claim**
- **v0.2.7 does not receive retroactive** `SHA256SUMS` assets
- Release trust still depends on **GitHub account security**, **branch protection** (if enabled), **tag discipline**, and **workflow integrity**
- Passing CI does not certify production readiness

## Verify this release

```bash
# Download SHA256SUMS and tarball from the v0.2.8 release page, then:
sha256sum -c SHA256SUMS
```

See [docs/artifact-verification.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/artifact-verification.md) and [docs/release-provenance.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/release-provenance.md).

## Prior releases

- [v0.2.7](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.7) — deployment reference profile
- [v0.2.6](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.6) — observability and audit review
- [v0.2.5](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.5) — safe LLM adapter interface

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
