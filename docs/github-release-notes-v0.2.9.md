## Summary

**v0.2.9** adds **P11 enterprise integration planning** and a **final release-readiness audit** on top of **v0.2.8** release provenance. This release is documentation and validation evidence only. The validation gate passed with **293** pytest tests.

This remains a **production-oriented defensive reference implementation**, not a managed production platform.

## What changed since v0.2.8

| Area | Change |
|------|--------|
| Enterprise planning (P11) | [enterprise-integration-plan.md](enterprise-integration-plan.md), identity/KMS/approval/SIEM/rate-limit guidance, [enterprise-readiness-checklist.md](enterprise-readiness-checklist.md) |
| Release-readiness audit | [reports/final-release-readiness-audit.md](../reports/final-release-readiness-audit.md) |
| Doc alignment | Operational checklists and diagrams aligned to **293** tests |
| Tests | **293** pytest tests (unchanged count from v0.2.8; honesty tests for enterprise and release docs on main) |

## P11: Enterprise integration planning

| Topic | Status in this repository |
|-------|---------------------------|
| OIDC / SAML | Planning guidance only; **not implemented** |
| Cloud KMS / HSM | Planning guidance only; **not implemented** |
| Persistent approval store | Lab in-memory model; **enterprise store not implemented** |
| Managed SIEM connector | JSONL audit logs and export guidance; **no connector implemented** |
| Distributed rate limiting | Request size limits in app; **distributed limits not implemented** |

## Final release-readiness audit

| Check | Result |
|-------|--------|
| `make validate` | Pass (**293** tests, host + Docker) |
| `make demo` | Pass |
| `validate_repo.py` / `validate_policy.py` | Pass |
| Docker build | Pass |
| Docker Compose pytest | **293** passed |
| Production Compose `config` | Pass |
| v0.2.8 `SHA256SUMS` | Verified (`llm-agent-control-plane-v0.2.8.tar.gz: OK`) |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 293 passed |
| docker compose pytest | 293 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on release commit | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- **No runtime control-plane behavior changes** in `src/agent_control_plane/`
- Simulated tools only; **no live external tool execution**
- **No live LLM API calls**
- **No secrets** added to the repository
- v0.2.8 tag and checksum assets unchanged
- **No signed-release claim** (checksums remain unsigned)

## Honest limitations

- **Not a managed production platform**
- **No enterprise IdP**, **no production KMS**, **no persistent approval store**, **no managed SIEM connector** in application code
- Release checksums are **unsigned**; no cosign, GPG, or SLSA attestation
- Enterprise deployment remains **operator-owned** (gateway IdP, KMS, SIEM forwarding, edge rate limits)
- Validation gate passed; project is **not** claimed bug-free

## Prior releases

- [v0.2.8](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.8) — release provenance and checksums
- [v0.2.7](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.7) — deployment reference profile
- [v0.2.6](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.6) — observability and audit review

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
