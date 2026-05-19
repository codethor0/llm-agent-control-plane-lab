# SIEM Onboarding Plan

**Status:** Documentation and JSONL audit logs only. **No managed SIEM connector is implemented.**

This plan extends [siem-export.md](siem-export.md) with enterprise onboarding steps. Operators own ingestion, detections, and response.

## Current JSONL audit logs

| Property | Detail |
|----------|--------|
| Format | Append-only JSONL per run |
| Writer | `audit_logger.py` |
| Redaction | Heuristic secret patterns before write |
| Correlation | `correlation_id` on events (P9) |
| Location | `ACP_AUDIT_LOG_DIR` (default under `var/audit`) |

**Not provided:** tamper-evident storage, signed shipping, or bundled forwarder agent.

## Required fields for SIEM

Map these fields in your parser (see [audit-event-taxonomy.md](audit-event-taxonomy.md)):

| Field | Use |
|-------|-----|
| `event_type` | Detection logic |
| `timestamp` | Timeline |
| `correlation_id` | Session stitching |
| `tenant_id`, `user_id` | Scope |
| `tool_name`, `stage` | Control-plane stage |
| `allowed` | Outcome |
| `reason` | Triage context (no secrets) |

## Field mapping (example)

| JSONL field | Common SIEM field |
|-------------|-------------------|
| `event_type` | `event.action` or custom `acp.event_type` |
| `correlation_id` | `trace.id` |
| `tenant_id` | `organization.id` |
| `user_id` | `user.id` |

Adjust to your platform schema (CEF, ECS, OCSF).

## Severity mapping (suggested)

| Event types | Suggested severity |
|-------------|-------------------|
| `output_filter_blocked`, `provenance_denied`, `cross_tenant_blocked` | medium |
| `api_auth_failure`, repeated `schema_validation_failed` | medium-high |
| `approval_denied` on destructive tools | high |
| `allowed` on `export_records` with approval | informational (verify expected) |

Tune per organizational risk appetite.

## Detection use cases

| Use case | Signal |
|----------|--------|
| Prompt injection attempt | `provenance_denied` + retrieved source |
| Credential leak attempt | `output_filter_blocked` |
| Auth brute force | Spike in `api_auth_failure` |
| Cross-tenant probe | `cross_tenant_blocked` |
| Policy bypass attempt | `tool_disabled` or `missing_provenance_denied` |
| Adapter misconfig | `adapter_failure` |

Sample queries in [siem-export.md](siem-export.md) use **fake tenant IDs** only.

## Retention

| Layer | Owner |
|-------|-------|
| Local JSONL files | Operator rotation (`ACP_AUDIT_RETENTION_DAYS` is guidance) |
| SIEM index | SOC retention policy |
| Legal hold | Compliance team |

## Alert routing

Define on-call routes for high-severity detections. This repository does not send pages or tickets.

## Triage ownership

| Role | Responsibility |
|------|----------------|
| SOC | Alert triage, correlation, escalation |
| App owner | Policy and broker behavior questions |
| Platform | Gateway auth failures, rate limit abuse |

See [audit-review-playbook.md](audit-review-playbook.md) and [operator-runbook.md](operator-runbook.md).

## Sample safe queries

Use synthetic data in test environments:

```text
event_type:provenance_denied AND tenant_id:tenant-a
event_type:api_auth_failure
correlation_id:"demo-correlation-001"
```

Do not paste production log lines into public issues.

## What is not implemented

- Managed SIEM connector (Splunk UF, Elastic Agent, Sentinel connector)
- Real-time HTTP log shipping from the app
- OpenTelemetry export
- Tamper-evident log chain

## Future managed connector options

If implemented later, prefer:

- Sidecar or daemon reading JSONL files (no app code change)
- Object storage + SIEM pull (S3 + Athena, etc.)
- Signed batches with operator-owned keys

Each option requires tests and SECURITY-CONTROLS matrix updates before claims.

## Related docs

- [enterprise-integration-plan.md](enterprise-integration-plan.md)
- [siem-export.md](siem-export.md)
- [audit-event-taxonomy.md](audit-event-taxonomy.md)
