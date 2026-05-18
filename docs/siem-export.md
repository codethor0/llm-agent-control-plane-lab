# SIEM Export Guidance

This project writes **append-only JSONL** audit logs. It does not ship a managed SIEM connector, agent, or cloud integration. Operators ingest logs into Splunk, Elastic, Microsoft Sentinel, or similar platforms using their standard file or HTTP collectors.

## Log locations

| Source | Default path |
|--------|----------------|
| API / pipeline | `ACP_AUDIT_LOG_DIR/api_events.jsonl` |
| CLI demo | Temporary path printed by `make demo` |
| Docker | Volume or tmpfs per Compose profile |

Set `ACP_AUDIT_LOG_DIR` and enforce retention per organizational policy (see `ACP_AUDIT_RETENTION_DAYS` as guidance only).

## JSONL format

One JSON object per line. Fields are documented in [audit-event-taxonomy.md](audit-event-taxonomy.md). Ingestion should parse JSON lines; do not treat the file as a single JSON array.

**Redaction expectations:** `policy_reason`, `approval_reason`, and serialized lines pass through pattern redaction (`sk-...`, JWT-like strings, PEM private keys). Operators must still restrict log access and avoid copying audit content into unsecured channels.

## Recommended ingestion fields

Index at minimum:

- `timestamp`
- `event_type`
- `correlation_id`
- `request_id`
- `tenant_id`
- `user_id`
- `allowed`
- `stage`
- `policy_reason`
- `tool_name`

Optional for detections: `output_finding_types`, `output_highest_severity`, `risk_level`, `human_approval_required`.

## Splunk example queries

Search blocked tool decisions:

```
index=control_plane sourcetype=json event_type=tool_blocked
| stats count by tenant_id, tool_name, policy_reason
```

Correlate one request:

```
index=control_plane correlation_id="corr-session-abc"
| sort timestamp
```

Cross-tenant alerts:

```
index=control_plane event_type=cross_tenant_blocked
| stats count by tenant_id, user_id
```

## Elastic (KQL-style) example queries

```
event_type: "output_filter_blocked" and allowed: false
```

```
event_type: "api_auth_failure"
| summarize count() by tenant_id
```

## Microsoft Sentinel / KQL example queries

```kql
ControlPlaneAudit
| where EventType == "provenance_denied"
| summarize Count=count() by TenantId, bin(TimeGenerated, 1h)
```

```kql
ControlPlaneAudit
| where EventType == "adapter_failure"
| project TimeGenerated, CorrelationId, PolicyReason
```

Map JSONL field names to your table schema at ingest time.

## Detection ideas

| Detection | Event types | Rationale |
|-----------|-------------|-----------|
| Cross-tenant access attempt | `cross_tenant_blocked` | Isolation violation |
| Untrusted context tool use | `provenance_denied` | Injection or RAG poisoning |
| Secret leakage attempt | `output_filter_blocked` | Model exfiltration pattern |
| Auth brute force (edge + app) | `api_auth_failure` | Credential abuse |
| Disabled adapter invoked | `adapter_failure` | Misconfiguration or premature live wiring |
| Policy bypass in prod | `vulnerable_path_simulation` | Wrong API path in production |

## Alert severity mapping

| Event type | Suggested alert severity |
|------------|-------------------------|
| `cross_tenant_blocked` | P1 |
| `output_filter_blocked` | P2 |
| `provenance_denied` | P2 |
| `adapter_failure` | P2 |
| `approval_denied` | P3 |
| `api_auth_failure` | P3 (rate-based) |
| `tool_blocked` | P4 (threshold) |
| `request_body_limit_blocked` | P4 (threshold) |

Tune thresholds per environment. Lab traffic is low-volume; production requires baseline learning.

## Retention guidance

| Tier | Suggestion |
|------|------------|
| Hot | 7-30 days for investigation |
| Warm | 90 days for compliance review |
| Cold | Per regulatory requirement |

This repository does not enforce retention; operators delete or archive `ACP_AUDIT_LOG_DIR` contents on schedule.

## Limitations

- No built-in SIEM agent or cloud forwarder
- No guaranteed field schema versioning across releases (review release notes on upgrades)
- Redaction is heuristic, not enterprise DLP
- Correlation across multiple hosts requires shared `correlation_id` from clients or load balancers
- Vulnerable path events are educational only

## Related documents

- [audit-event-taxonomy.md](audit-event-taxonomy.md)
- [audit-review-playbook.md](audit-review-playbook.md)
- [production-hardening.md](production-hardening.md)
