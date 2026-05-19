# Production Deployment Hardening

This document describes how to deploy **llm-agent-control-plane** with a production-oriented security profile. The project remains a **defensive reference implementation**: it demonstrates control-plane patterns with simulated tools only. It is **not** a fully managed production service.

## What this project is

- An external control plane around a simulated LLM agent core
- Deny-by-default policy, tool broker authorization, provenance checks, approval gates, output filtering, and audit logging
- Local and container validation with 271 automated security tests

## What this project is not

- A drop-in production agent platform with enterprise IdP, workflow UI, or DLP
- A live LLM integration (adapter interface only; `ACP_ALLOW_LIVE_LLM_CALLS` is rejected; see [llm-adapter.md](llm-adapter.md))
- Certified for regulated production without your own organizational review

## Required controls before network exposure

| Control | Implementation | Notes |
|---------|----------------|-------|
| API authentication | `ACP_REQUIRE_API_AUTH=true` + API keys file | Lab uses file-based keys; production should use a secret manager |
| Explicit CORS | `ACP_ALLOWED_ORIGINS` (no `*` in production) | Enforced at config validation |
| Request size limit | `ACP_MAX_REQUEST_BODY_BYTES` | Middleware rejects oversized `Content-Length` |
| Safe error responses | `ACP_ENABLE_DEBUG_ERRORS=false` in production | No stack traces or verbose validation payloads |
| Simulated tools only | `ACP_ALLOW_LIVE_EXTERNAL_TOOLS=false` | Fail-closed if enabled |
| Shell tools disabled | `ACP_ALLOW_SHELL_TOOLS=false` | Fail-closed if enabled |
| Policy integrity | `policies/default.yaml` + SHA-256 | Run `python scripts/validate_policy.py` |
| TLS termination | Reverse proxy (nginx, Envoy, cloud LB) | Not terminated inside the demo app |
| Rate limiting | External gateway or service mesh | `ACP_ENABLE_RATE_LIMIT_GUIDANCE` documents requirement; not built into app |

## Configuration reference

Environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `ACP_ENVIRONMENT` | `local`, `test`, or `production` |
| `ACP_REQUIRE_API_AUTH` | Require `X-API-Key` or `Authorization: Bearer` on `/run` |
| `ACP_ALLOWED_API_KEYS_FILE` | Path to newline-separated API keys (no comments with secrets in logs) |
| `ACP_API_KEY` | Optional single inline key (prefer file + secret manager in production) |
| `ACP_ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `ACP_MAX_REQUEST_BODY_BYTES` | Maximum request body size (default 1 MiB) |
| `ACP_AUDIT_LOG_DIR` | Directory for JSONL audit files |
| `ACP_AUDIT_RETENTION_DAYS` | Retention guidance (operator-enforced) |
| `ACP_ENABLE_STRICT_PROVENANCE` | Require HMAC provenance signatures |
| `ACP_PROVENANCE_HMAC_KEY_FILE` | Path to HMAC key bytes (production strict mode) |
| `ACP_REQUIRE_APPROVAL_TOKEN` | Broker requires bound approval tokens |
| `ACP_ENABLE_DEBUG_ERRORS` | Verbose errors (disallowed in production profile) |
| `ACP_LLM_ADAPTER_MODE` | `simulated` (default) or `disabled_external` (fail-closed stub) |
| `ACP_ALLOW_LIVE_LLM_CALLS` | Must remain `false` (not implemented; validation fails if `true`) |
| `ACP_LLM_PROVIDER_NAME` | Optional label for future providers (metadata only) |
| `ACP_LLM_MODEL_NAME` | Optional model label (metadata only) |

Load and validate in code:

```python
from agent_control_plane.config import load_config_from_env

config = load_config_from_env()
config.validate()
```

## API auth boundary

- `/health` — no authentication (load balancers and orchestrators)
- `/run` — requires API key when `ACP_REQUIRE_API_AUTH=true`
- Keys are compared with constant-time-safe membership check; keys are never logged
- Do not commit real keys; use `.gitignore` for key files and mount secrets at runtime

## CORS policy

- Local mode allows `http://127.0.0.1:8080` and `http://localhost:8080` by default
- Production mode rejects wildcard origins and empty origin lists
- Configure only the front-end origins that must call the API

## Request size limits

`MaxBodySizeMiddleware` rejects requests when `Content-Length` exceeds `ACP_MAX_REQUEST_BODY_BYTES`. Combine with reverse-proxy body limits for defense in depth.

## Audit and observability

- JSONL audit logs: `ACP_AUDIT_LOG_DIR` (default `./audit_logs`)
- Events include `correlation_id` for request tracing (header `X-Correlation-ID` or body field)
- Event taxonomy: [audit-event-taxonomy.md](audit-event-taxonomy.md)
- SIEM ingestion guidance: [siem-export.md](siem-export.md) (documentation only; no bundled connector)
- Review playbooks: [audit-review-playbook.md](audit-review-playbook.md), [operator-runbook.md](operator-runbook.md)

## Rate limiting recommendation

Deploy rate limiting at the edge (API gateway, reverse proxy, or service mesh). The application exposes `ACP_ENABLE_RATE_LIMIT_GUIDANCE` as a documented reminder; per-tenant and per-IP limits are an operator responsibility.

## TLS and reverse proxy assumptions

- Terminate TLS at the proxy; forward to the app over loopback or private network
- Set `X-Forwarded-*` headers only from trusted proxies
- Do not expose the demo API directly to the public internet without auth, TLS, and organizational review

## Container hardening

The `Dockerfile`, `docker-compose.yml`, and reference `docker-compose.production.yml` implement:

- Non-root `appuser` runtime
- `read_only` root filesystem in Compose with `tmpfs` for `/tmp` and `/app/var`
- `security_opt: no-new-privileges:true`
- Debian security upgrades during image build
- `HEALTHCHECK` validates configuration import and validation
- No shell entrypoint executing model-provided commands

Writable paths: `/app/var/audit` (tmpfs in Compose), `/tmp` for process temp files.

## Audit log storage and retention

- Default audit directory: `audit_logs/` (local) or `ACP_AUDIT_LOG_DIR`
- JSONL events with redaction (see `audit_logger.py`)
- `ACP_AUDIT_RETENTION_DAYS` is validated and documented; implement rotation/archival with your log platform
- Protect audit files from tampering (append-only storage, SIEM forwarding, object-lock buckets)

## Key management requirements

| Secret | Requirement |
|--------|-------------|
| API keys | Secret manager or mounted file; rotate on compromise |
| Provenance HMAC key | Required when strict provenance is enabled in production |
| Policy signing | Future: organizational policy signing beyond SHA-256 drift detection |

## Approval workflow requirements

When `ACP_REQUIRE_APPROVAL_TOKEN=true`, the broker requires bound, one-time approval tokens (lab in-memory registry). Production deployments need a persistent approval store and IdP-integrated workflow UI.

## Provenance signing requirements

When `ACP_ENABLE_STRICT_PROVENANCE=true`, configure `ACP_PROVENANCE_HMAC_KEY_FILE` with key material from a secret manager. Lab HMAC is not production PKI.

## Observability requirements

- Forward structured audit JSONL to SIEM
- Add OpenTelemetry or equivalent at the proxy and application (roadmap item)
- Alert on broker deny spikes, output-filter blocks, and auth failures
- Never log raw API keys, approval tokens, or unredacted secrets

## Incident response notes

1. Rotate API and provenance keys if exposure is suspected
2. Review audit JSONL for allow/deny anomalies
3. Re-run `make validate` and supply-chain workflows before redeploy
4. Do not enable `ACP_ALLOW_LIVE_EXTERNAL_TOOLS` or `ACP_ALLOW_SHELL_TOOLS` as a workaround

## Unsafe deployment examples (avoid)

- `ACP_ENVIRONMENT=production` without API keys or auth
- Wildcard CORS (`*`) in production
- `ACP_ENABLE_DEBUG_ERRORS=true` on a network-facing host
- Binding `0.0.0.0` without TLS and without API auth
- Mounting writable host paths into the container as root
- Committing `.env` with real API keys

## Production readiness checklist

- [ ] `ACP_ENVIRONMENT=production` and `config.validate()` passes at startup
- [ ] API auth enabled with keys from secret manager
- [ ] Explicit `ACP_ALLOWED_ORIGINS` (no wildcard)
- [ ] `ACP_ENABLE_DEBUG_ERRORS=false`
- [ ] `ACP_ALLOW_LIVE_EXTERNAL_TOOLS=false` and `ACP_ALLOW_SHELL_TOOLS=false`
- [ ] TLS terminated at reverse proxy
- [ ] Rate limiting at edge
- [ ] Policy integrity verified (`validate_policy.py`)
- [ ] Container runs as non-root with read-only rootfs where possible
- [ ] Audit logs forwarded and retention enforced
- [ ] Supply-chain CI green (CodeQL, Gitleaks, Trivy, SBOM)
- [ ] Organizational security review completed
- [ ] No claim of universal LLM safety or production certification

## Deployment reference profile (P10)

- [docker-compose.production.yml](../docker-compose.production.yml) — API with auth, read-only rootfs, audit volume
- [.env.production.example](../.env.production.example) — fake production variables
- [deploy/kubernetes/README.md](../deploy/kubernetes/README.md) — reference manifests
- [deployment-boundaries.md](deployment-boundaries.md) — app vs operator responsibilities
- [deployment-checklist.md](deployment-checklist.md) — deploy validation steps
- [helm-guidance.md](helm-guidance.md) — Helm values patterns (no bundled chart)

## Related documentation

- [deployment-threat-model.md](deployment-threat-model.md)
- [release-security-checklist.md](release-security-checklist.md)
- [supply-chain.md](supply-chain.md)
- [SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md)
