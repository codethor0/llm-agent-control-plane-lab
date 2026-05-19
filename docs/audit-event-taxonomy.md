# Audit Event Taxonomy

Structured JSONL audit events support security monitoring, incident response, and SIEM ingestion. All events are written by `AuditLogger` with automatic redaction of secret-like patterns.

**Invariant:** audit events record decisions and metadata only; they never store raw API keys, passwords, or full prompt text.

## Common fields

| Field | Required | Description |
|-------|----------|-------------|
| `event_type` | yes | Stable classifier for detections and dashboards |
| `timestamp` | yes | UTC ISO-8601 (added at write time) |
| `correlation_id` | yes | Ties all events for one logical request or API call |
| `request_id` | yes | Per-turn identifier from `AgentRequest` or API fallback |
| `user_id` | yes | Subject identifier (or `unknown` for API boundary events) |
| `session_id` | yes | Session identifier |
| `tenant_id` | yes | Tenant scope |
| `model` | yes | Model label (`simulated-v1` or `n/a` for API events) |
| `stage` | yes | Pipeline or API stage where the decision occurred |
| `allowed` | yes | Whether the action proceeded |
| `policy_decision` | yes | `allow` or `deny` (or `bypassed` on vulnerable path simulation) |
| `policy_reason` | yes | Redacted human-readable reason |
| `tool_name` | optional | Tool involved, if any |
| `target` | optional | Tool target, if any |
| `risk_level` | optional | Policy risk label |
| `source_context_ids` | optional | Provenance context IDs |
| `retrieved_context_trust` | optional | Trust label for retrieved context |
| `human_approval_required` | yes | Whether approval was required |
| `contains_sensitive_data` | yes | Output-filter sensitivity flag |
| `output_*` fields | optional | Redacted output-filter metadata only |

Optional approval fields: `approval_id`, `approver_id`, `approval_decision`, `approval_reason`, `approval_token_valid`, `approval_token_failure_reason`.

## Event catalog

### tool_allowed

| Attribute | Value |
|-----------|-------|
| Severity | info |
| Category | authorization |
| Stage | `tool_broker` / `simulation` |
| Detection | Baseline allow telemetry; verify expected tools and tenants |
| Response | None required if policy-approved; investigate unexpected high-risk tools |

**Example (redacted):**

```json
{"event_type":"tool_allowed","correlation_id":"req-1","request_id":"req-1","allowed":true,"policy_decision":"allow","policy_reason":"allowed","tool_name":"read_records","stage":"simulation"}
```

### tool_blocked

| Attribute | Value |
|-----------|-------|
| Severity | medium |
| Category | policy |
| Stage | `tool_broker` |
| Detection | Policy denial for disabled or unknown tools |
| Response | Review policy reason; confirm not prompt-injection driven misuse |

### provenance_denied

| Attribute | Value |
|-----------|-------|
| Severity | high |
| Category | provenance |
| Stage | `tool_broker` |
| Detection | Untrusted context attempted to authorize a tool |
| Response | Inspect `source_context_ids` and scenario; check RAG/tool-output ingestion |

### approval_denied

| Attribute | Value |
|-----------|-------|
| Severity | medium |
| Category | approval |
| Stage | `tool_broker` |
| Detection | High-impact tool without valid human approval or token |
| Response | Confirm workflow; issue approval token if legitimate |

### output_filter_blocked

| Attribute | Value |
|-----------|-------|
| Severity | high |
| Category | data_loss_prevention |
| Stage | `output_filter` |
| Detection | Model output matched leak heuristics before broker |
| Response | Review `output_findings_redacted` only; do not paste raw model text into tickets |

### schema_validation_failed

| Attribute | Value |
|-----------|-------|
| Severity | medium |
| Category | structure |
| Stage | `schema_validation` |
| Detection | Malformed tool-call payload |
| Response | Treat as untrusted model output; no authorization implied |

### cross_tenant_blocked

| Attribute | Value |
|-----------|-------|
| Severity | critical |
| Category | tenant_isolation |
| Stage | `tool_broker` |
| Detection | Cross-tenant target or context mismatch |
| Response | Escalate; preserve audit log; review tenant binding |

### model_response_allowed

| Attribute | Value |
|-----------|-------|
| Severity | info |
| Category | model_output |
| Stage | `complete` |
| Detection | Turn completed without tool call |
| Response | None |

### adapter_failure

| Attribute | Value |
|-----------|-------|
| Severity | high |
| Category | llm_adapter |
| Stage | `llm_adapter` |
| Detection | External adapter disabled or misconfigured |
| Response | Verify `ACP_LLM_ADAPTER_MODE`; do not enable live calls without review |

### api_auth_failure

| Attribute | Value |
|-----------|-------|
| Severity | medium |
| Category | api_boundary |
| Stage | `api_auth` |
| Detection | Missing or invalid API key on `/run` |
| Response | Check client credentials; watch for brute force at edge |

### request_body_limit_blocked

| Attribute | Value |
|-----------|-------|
| Severity | low |
| Category | api_boundary |
| Stage | `api_middleware` |
| Detection | Oversized HTTP body |
| Response | Tune client or proxy limits; possible DoS probe |

### vulnerable_path_simulation

| Attribute | Value |
|-----------|-------|
| Severity | info |
| Category | education |
| Stage | `vulnerable_simulation` |
| Detection | Lab vulnerable path used (no broker) |
| Response | Ensure not used in production deployments |

### repo_hygiene_failure (CI)

| Attribute | Value |
|-----------|-------|
| Severity | medium |
| Category | supply_chain |
| Stage | `ci` / `validate_repo` |
| Detection | Prompt artifact or forbidden file pattern in repository |
| Response | Remove artifact; re-run `python scripts/validate_repo.py` |

Not emitted by runtime pipeline; documented for operator and CI correlation.

## Severity guidance

| Severity | Use when |
|----------|----------|
| critical | Cross-tenant or isolation breach |
| high | Provenance bypass attempt, output leak block, adapter failure |
| medium | Policy deny, approval deny, schema failure, API auth failure |
| low | Body limit, informational allows |
| info | Expected allows, lab vulnerable path |

## Related documents

- [siem-export.md](siem-export.md)
- [audit-review-playbook.md](audit-review-playbook.md)
- [operator-runbook.md](operator-runbook.md)
