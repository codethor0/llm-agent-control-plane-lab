# GitHub Publication Readiness

Status: **published** (verified end-to-end May 2026).

## Repository state

| Check | Status |
|-------|--------|
| Public repository | https://github.com/codethor0/llm-agent-control-plane-lab |
| Git remote | `origin` configured |
| Latest release | [v0.1.1](https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.1) |
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
| Latest release notes | [github-release-notes-v0.1.1.md](github-release-notes-v0.1.1.md) |
| Architecture diagram | [assets/llm-agent-control-plane.svg](assets/llm-agent-control-plane.svg) |
| Social launch copy | [social/](social/) |

## Claims discipline

Do not describe this lab as production-ready, exploit tooling, or formally verified. Simulated tools only; see [provenance.md](provenance.md) for declarative (unsigned) provenance.
