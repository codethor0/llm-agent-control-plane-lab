# GitHub Publication Readiness

Status: **published** (verified end-to-end May 2026).

## Repository state

| Check | Status |
|-------|--------|
| Public repository | https://github.com/codethor0/llm-agent-control-plane |
| Git remote | `origin` configured |
| Latest release | [v0.2.8](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.8) |
| CI badge | Enabled on README |
| License | MIT |

## Validation baseline

```bash
make validate
make demo
python scripts/validate_repo.py
```

Expected: pytest passes (see README for current count), Docker pytest passes, repo hygiene OK.

## Key artifacts

| Artifact | Location |
|----------|----------|
| Security controls matrix | [SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md) |
| Release checklist | [release-checklist.md](release-checklist.md) |
| Latest release notes | [github-release-notes-v0.2.8.md](github-release-notes-v0.2.8.md) |
| Architecture diagram | [assets/llm-agent-control-plane.svg](assets/llm-agent-control-plane.svg) |
| Repo logo | [assets/llm-agent-control-plane-logo.svg](assets/llm-agent-control-plane-logo.svg) |

## Claims discipline

Do not describe this lab as production-ready, exploit tooling, or formally verified. Simulated tools only; see [provenance.md](provenance.md) for declarative (unsigned) provenance.
