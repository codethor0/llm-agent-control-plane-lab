## Summary

**v0.2.9** completes **P11: enterprise integration planning**. This release adds operator-facing documentation for identity (OIDC/SAML), KMS and secret management, persistent approval workflows, SIEM onboarding, rate limiting and edge controls, and an enterprise readiness checklist. Documentation tests guard against false claims that these capabilities are implemented in the lab runtime.

This remains a **production-oriented defensive reference implementation**, not a managed production platform.

## What changed since v0.2.8

| Area | Change |
|------|--------|
| Docs | [enterprise-integration-plan.md](enterprise-integration-plan.md), [enterprise-readiness-checklist.md](enterprise-readiness-checklist.md) |
| Identity / secrets | [identity-integration.md](identity-integration.md), [kms-secret-management.md](kms-secret-management.md) |
| Approvals / SIEM / edge | [approval-workflow.md](approval-workflow.md), [siem-onboarding-plan.md](siem-onboarding-plan.md), [rate-limiting-edge-controls.md](rate-limiting-edge-controls.md) |
| Cross-links | README, ROADMAP, SECURITY-CONTROLS, deployment and release checklists, security gap assessment, production hardening |
| Container image | Dockerfile copies new enterprise guidance into the image for offline reference |
| Tests | **293** pytest tests (was 282 on v0.2.8) |

## P11: Enterprise integration planning

| Topic | Status in this repository |
|-------|---------------------------|
| OIDC / SAML | Planning guidance only; **not implemented** |
| Cloud KMS / HSM | Planning guidance only; **not implemented** |
| Persistent approval store | Lab in-memory model; **enterprise store not implemented** |
| Managed SIEM connector | JSONL audit logs and export guidance; **no connector implemented** |
| Distributed rate limiting | Request size limits documented; **distributed limits not implemented** |
| Production boundaries | Operator-owned IdP, KMS, SIEM, edge, and approval systems |

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
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- **No runtime control-plane behavior changes** in `src/agent_control_plane/`
- Simulated tools only; **no live external tool execution**
- **No live LLM API calls**
- **No secrets** added to the repository
- Policy canonical hash unchanged from v0.2.8
- v0.2.8 and earlier release tags unchanged

## Honest limitations

- Enterprise docs describe **what operators must build or integrate**; they do not add IdP, KMS, SIEM, or edge enforcement to the lab
- **No OIDC/SAML login**, **no cloud KMS integration**, **no managed SIEM agent**, **no distributed rate limiter** in application code
- Approval workflow remains the **in-lab human gate**; no multi-tenant approval API or revocation admin UI
- Passing CI and documentation tests do **not** certify enterprise production readiness
- README **latest release** remains **v0.2.8** until a separate release promotion step tags v0.2.9

## Prior releases

- [v0.2.8](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.8) — release provenance and checksums
- [v0.2.7](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.7) — deployment reference profile
- [v0.2.6](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.6) — observability and audit review

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
