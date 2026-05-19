# Audit Review Playbook

Operational guide for reviewing control-plane audit JSONL. This lab does not provide a hosted review UI or managed SOC service.

## Daily review checklist

1. Confirm audit log directory is writable and growing (`ACP_AUDIT_LOG_DIR`).
2. Sample last 24 hours of events; verify `timestamp` ordering.
3. Count `event_type` distribution; spikes in `tool_blocked` or `api_auth_failure` warrant follow-up.
4. Verify no `vulnerable_path_simulation` in production-labelled environments.
5. Confirm `cross_tenant_blocked` count is zero in steady state.
6. Spot-check `output_filter_blocked` events use `output_findings_redacted` only.
7. Re-run `python scripts/validate_repo.py` if repository changes occurred.

## Release review checklist

Before tagging a release:

1. `make validate` green (host and Docker).
2. Policy hash matches: `python scripts/validate_policy.py`.
3. GitHub Actions: CI, CodeQL, Secret scan, Trivy, SBOM success on `main`.
4. Review diff for new `event_type` values; update [audit-event-taxonomy.md](audit-event-taxonomy.md) if added.
5. Confirm release notes state limitations (simulated tools, no live LLM by default).
6. No prompt artifacts in commit history for the release branch.

## Incident review checklist

When investigating a suspected control-plane bypass or data issue:

1. **Preserve evidence:** copy JSONL files read-only; record `correlation_id` and time range.
2. **Reconstruct flow:** filter all events with the same `correlation_id`; sort by `timestamp`.
3. **Identify terminal event:** last `allowed: false` or unexpected `allowed: true`.
4. **Do not** paste raw model output or user messages from non-audit sources into public tickets.
5. **Map to taxonomy:** use [audit-event-taxonomy.md](audit-event-taxonomy.md) for severity and response.
6. **Validate configuration:** `ACP_ENVIRONMENT`, auth flags, adapter mode, policy file hash.
7. **Escalate** cross-tenant, repeated provenance denies, or output filter blocks on production paths.

## Interpreting blocked decisions

| event_type | Meaning | Investigate |
|------------|---------|-------------|
| `tool_blocked` | Policy denied tool | Policy YAML, role, tool enablement |
| `provenance_denied` | Context cannot authorize | RAG chunks, tool-output segments, provenance source |
| `approval_denied` | Missing or invalid approval | Approval workflow, token registry |
| `schema_validation_failed` | Bad tool-call shape | Model output quality; not authorization |
| `output_filter_blocked` | Leak heuristic match | Redacted findings only; DLP tuning |
| `cross_tenant_blocked` | Tenant mismatch | Target tenant, request tenant, policy |
| `adapter_failure` | LLM adapter fail-closed | `ACP_LLM_ADAPTER_MODE`; no live provider wired |
| `api_auth_failure` | API key rejected | Client config, rotation, edge rate limits |
| `request_body_limit_blocked` | Oversized body | Client bug or DoS probe |

## Approval denials

- Check `human_approval_required` and `approval_decision`.
- Token failures include `approval_token_failure_reason` (redacted).
- Legitimate operations require human approval per policy (`send_email`, `export_records`, etc.).
- Deny is expected when `human_approval` is false in the request.

## Cross-tenant blocks

Treat as **high priority**. Confirm:

- `tenant_id` on request matches tool `target` and provenance `tenant_id`.
- No policy regression in `policies/default.yaml`.
- Not a test scenario running against production config.

## Output filter blocks

- Use `output_finding_types` and `output_highest_severity` for triage.
- Inspect `output_findings_redacted` array only.
- Do not disable output filtering to unblock workflows without security review.

## Escalation criteria

| Condition | Action |
|-----------|--------|
| Any `cross_tenant_blocked` in production | Escalate to security lead |
| Sustained `provenance_denied` from one tenant | Review ingestion and RAG trust |
| `output_filter_blocked` with critical severity | Incident channel; preserve logs |
| `adapter_failure` after config change | Roll back adapter mode |
| `vulnerable_path_simulation` in production API | Misconfiguration; disable path |

## Evidence preservation

1. Copy JSONL with checksum (SHA-256).
2. Record git commit, policy hash, and `ACP_*` env snapshot (no secrets).
3. Restrict access to audit copies.
4. Retain per organizational retention policy.

## Related documents

- [siem-export.md](siem-export.md)
- [operator-runbook.md](operator-runbook.md)
- [deployment-threat-model.md](deployment-threat-model.md)
