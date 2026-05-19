# Deployment Boundaries

This table clarifies what the application enforces, what the container/CI stack supports, and what **operators must provide**. This project is a **production-oriented defensive reference implementation**, not a drop-in production platform.

| Control | Enforced by app | Enforced by container | Enforced by CI | Operator must provide | Notes |
|---------|-----------------|----------------------|----------------|----------------------|-------|
| API auth on `/run` | Yes (when configured) | No | No | Keys, rotation, IdP integration | `/health` unauthenticated for probes |
| CORS allowlist | Yes (production profile) | No | No | Correct origin list | Wildcard blocked in production |
| Request body limits | Yes (middleware) | No | No | Proxy limits (defense in depth) | `ACP_MAX_REQUEST_BODY_BYTES` |
| Strict provenance HMAC | Yes (optional) | No | No | Key material from KMS/secret manager | Lab key is not PKI |
| Approval tokens | Yes (optional) | No | No | Persistent store, workflow UI | Lab registry is in-memory |
| Live LLM disabled | Yes (validation) | No | No | Adapter choice | No live provider client in repo |
| Shell tools disabled | Yes (validation + policy) | No | No | Policy content | `run_shell` disabled in default policy |
| Simulated tools only | Yes | No | No | Do not wire real executors | By design |
| Audit JSONL logging | Yes | Writable volume/tmpfs | No | Retention, SIEM forwarding, access control | Redaction in app |
| Audit retention | Validated only | No | No | Archival and deletion jobs | `ACP_AUDIT_RETENTION_DAYS` |
| SIEM ingestion | No | No | No | Connectors, parsers, alerts | See [siem-export.md](siem-export.md) |
| TLS | No | No | No | Ingress, reverse proxy, cert manager | Terminate TLS outside app |
| Rate limiting | No (guidance flag) | No | No | Gateway, mesh, WAF | `ACP_ENABLE_RATE_LIMIT_GUIDANCE` |
| Enterprise IdP | No | No | No | OIDC/SAML integration at edge | API keys are lab-style file keys |
| KMS / secret manager | No | No | No | Mount secrets at runtime | No secrets in image |
| Persistent approvals | No | No | No | Database or workflow service | Not in reference manifests |
| Network isolation | No | Optional NetworkPolicy (reference) | No | Platform networking policy | K8s manifest is reference-only |
| Non-root runtime | No | Yes (Dockerfile/K8s reference) | Docker pytest | Platform admission | `appuser` in image |
| Read-only rootfs | No | Yes (Compose/K8s reference) | No | Writable audit mount | tmpfs or volume for `/tmp/audit` |
| Policy integrity SHA-256 | Yes (script) | No | Yes (`validate_policy.py`) | Deploy correct policy file | `policies/default.sha256` |
| Supply-chain scans | No | Image build | Yes (CodeQL, Gitleaks, Trivy, SBOM) | Triage and upgrade | Not formal certification |
| Branch protection | No | No | No | GitHub org settings | Documented as operator responsibility |
| OpenTelemetry traces | No | No | No | APM integration | Roadmap item |
| Production certification claim | No | No | No | Organizational review | Docs state limitations explicitly |

## Reference artifacts (P10)

| Artifact | Purpose |
|----------|---------|
| `docker-compose.production.yml` | Compose profile with auth, read-only rootfs, audit volume |
| `.env.production.example` | Fake production environment variables |
| `deploy/kubernetes/*` | Reference manifests (not continuously deployed) |
| [helm-guidance.md](helm-guidance.md) | Values patterns without bundled chart |
| [deployment-checklist.md](deployment-checklist.md) | Pre-flight and post-deploy checks |

## Enterprise integration (P11)

P11 adds **guidance only** for IdP, KMS, persistent approvals, SIEM onboarding, and edge rate limiting. None of these are implemented in application code. See [enterprise-integration-plan.md](enterprise-integration-plan.md) and [enterprise-readiness-checklist.md](enterprise-readiness-checklist.md).

## Related documents

- [production-hardening.md](production-hardening.md)
- [deployment-threat-model.md](deployment-threat-model.md)
- [operator-runbook.md](operator-runbook.md)
- [enterprise-integration-plan.md](enterprise-integration-plan.md)
