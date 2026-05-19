# Deployment Checklist

Use before and after deploying the control-plane API in any shared or network-facing environment. This project remains a **reference implementation**; organizational sign-off is required for production use.

## Pre-deploy validation

- [ ] `make validate` passes on the release commit you are deploying
- [ ] `make demo` completes seven scenarios
- [ ] `python scripts/validate_repo.py` passes (no prompt artifacts)
- [ ] `python scripts/validate_policy.py` passes (hash matches)
- [ ] Docker image built from tagged release: `docker compose build`
- [ ] Docker tests pass: `docker compose run --rm app python -m pytest`
- [ ] Supply-chain workflows green on release tag (CI, CodeQL, Secret scan, Trivy, SBOM)

## Environment validation

- [ ] `ACP_ENVIRONMENT=production`
- [ ] `ACP_REQUIRE_API_AUTH=true` with keys from secret manager (not committed)
- [ ] `ACP_ALLOWED_ORIGINS` lists only required front-end origins (no `*`)
- [ ] `ACP_ENABLE_DEBUG_ERRORS=false`
- [ ] `ACP_ALLOW_LIVE_EXTERNAL_TOOLS=false`
- [ ] `ACP_ALLOW_SHELL_TOOLS=false`
- [ ] `ACP_LLM_ADAPTER_MODE=simulated`
- [ ] `ACP_ALLOW_LIVE_LLM_CALLS=false`
- [ ] Application startup runs `config.validate()` successfully

## Container / platform validation

- [ ] Container runs as non-root (`appuser` or equivalent `securityContext`)
- [ ] Root filesystem read-only where compatible; audit path writable via volume or tmpfs
- [ ] No secrets baked into image layers
- [ ] Resource requests/limits set (Kubernetes) or host constraints understood (Compose)
- [ ] Reference profile reviewed: `docker-compose.production.yml` or `deploy/kubernetes/`

## API and network validation

- [ ] `/health` returns 200 without auth
- [ ] `/run` returns 401 without API key when auth required
- [ ] `/run` succeeds with valid lab-fake or production key from secret mount
- [ ] TLS terminated at reverse proxy or Ingress (not optional for internet exposure)
- [ ] Rate limiting configured at edge
- [ ] Service not bound to `0.0.0.0` on the public internet without TLS and auth
- [ ] CORS preflight from allowed origin succeeds; disallowed origin blocked

## Audit and observability validation

- [ ] `ACP_AUDIT_LOG_DIR` writable and on durable storage or forwarded promptly
- [ ] Audit JSONL contains `correlation_id` and `event_type`
- [ ] Test deny scenario produces expected `event_type` (e.g. `tool_blocked`)
- [ ] No API keys or raw secrets in audit file sample review
- [ ] SIEM onboarding documented per [siem-export.md](siem-export.md) (operator-owned)
- [ ] Retention and archival job defined (`ACP_AUDIT_RETENTION_DAYS` is guidance only)

## Security process validation

- [ ] Incident response owner assigned
- [ ] Rollback plan documented (previous image tag and policy hash)
- [ ] Release image/tag pinned (not `:latest` in production)
- [ ] No prompt artifacts or real secrets in repository or ConfigMaps
- [ ] Branch protection enabled on `main` (org setting; not enforced by app)
- [ ] [deployment-boundaries.md](deployment-boundaries.md) reviewed with platform team

## Post-deploy smoke test

```bash
curl -s http://127.0.0.1:8080/health
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8080/run \
  -H 'Content-Type: application/json' \
  -d '{"request_id":"deploy-smoke-1","user_id":"u","session_id":"s","tenant_id":"tenant-a","user_message":"read","scenario":"safe_read","path":"protected"}'
# Expect 401 when auth required
```

## Honest limitations

- Not a managed production service
- No bundled Helm chart, SIEM agent, IdP, KMS, or persistent approval store
- Kubernetes manifests are reference-only

## Related documents

- [production-hardening.md](production-hardening.md)
- [operator-runbook.md](operator-runbook.md)
- [audit-review-playbook.md](audit-review-playbook.md)
- [release-security-checklist.md](release-security-checklist.md)
