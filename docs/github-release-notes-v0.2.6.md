## Summary

**v0.2.6** adds observability and audit review: `correlation_id` on every JSONL audit event, operational API and adapter audit events, event taxonomy, SIEM export guidance, audit review playbooks, and an operator runbook.

This remains a **production-oriented defensive reference implementation**, not a drop-in production service with managed monitoring.

## What changed since v0.2.5

| Area | Change |
|------|--------|
| Correlation | `correlation_id` on all audit events; `X-Correlation-ID` header and body field |
| API audit | `api_auth_failure`, `request_body_limit_blocked` (no API keys in logs) |
| Adapter audit | `adapter_failure` on `LLMAdapterError` (no prompts or secrets in logs) |
| Observability | `observability.py` helpers |
| Docs | [audit-event-taxonomy.md](audit-event-taxonomy.md), [siem-export.md](siem-export.md), [audit-review-playbook.md](audit-review-playbook.md), [operator-runbook.md](operator-runbook.md) |
| Tests | **260** pytest tests (was 248 on v0.2.5) |

## P9: Observability and audit review

| Control | Implementation |
|---------|----------------|
| Correlation ID | Defaults to `request_id`; optional header/body override |
| Event taxonomy | Documented types, severity, detection use cases |
| SIEM guidance | Splunk, Elastic, Sentinel/KQL examples (documentation only) |
| Review playbooks | Daily, release, and incident checklists |
| Operator runbook | Startup, validation, logs, CI/supply-chain failure response |
| Redaction | API keys and secrets not written to audit on auth failure |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 260 passed |
| docker compose pytest | 260 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- Simulated tools only; **no live external tool execution**
- **No live LLM API calls**
- **No managed SIEM connector** or OpenTelemetry traces
- v0.2.5 and earlier release tags unchanged

## Honest limitations

- **JSONL logs only** — retention enforced by operators (`ACP_AUDIT_LOG_DIR`)
- **SIEM guidance only** — no bundled agent, forwarder, or cloud integration
- **No managed monitoring platform** — alert tuning and IR ownership remain with the deploying organization
- Heuristic redaction, not enterprise DLP
- Operational gaps unchanged: enterprise IdP, persistent approvals, production KMS, edge rate limiting, reviewed live LLM adapters

## Upgrade notes

- Pass `X-Correlation-ID` or `correlation_id` in `/run` body to tie multi-event flows in your SIEM
- Review [docs/audit-event-taxonomy.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/audit-event-taxonomy.md) when building detections

## Prior releases

- [v0.2.5](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.5) — safe LLM adapter interface
- [v0.2.4](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.4) — production deployment hardening
- [v0.2.3](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.3) — supply-chain hardening

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md) and [docs/audit-review-playbook.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/audit-review-playbook.md).
