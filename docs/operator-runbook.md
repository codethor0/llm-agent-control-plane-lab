# Operator Runbook

Day-two operations for the llm-agent-control-plane lab API and validation toolchain. Simulated tools only; not a managed production service.

## Startup checks

1. Python 3.12: `.venv/bin/python scripts/check_python_version.py`
2. Policy present: `policies/default.yaml` and `policies/default.sha256`
3. Environment: copy `.env.example` to `.env` for local runs (no real secrets)
4. `ACP_ENVIRONMENT` matches intent (`local` vs `production`)
5. `ACP_LLM_ADAPTER_MODE=simulated` (default)
6. `ACP_ALLOW_LIVE_LLM_CALLS=false`

## Validation checks

```bash
make validate
make demo
python scripts/validate_repo.py
python scripts/validate_policy.py
```

Expected: all pass; pytest count matches README; demo writes seven scenarios.

## Log location

| Variable | Purpose |
|----------|---------|
| `ACP_AUDIT_LOG_DIR` | Directory for `api_events.jsonl` |
| `AUDIT_LOG_PATH` | Legacy demo path hint in `.env.example` |

List recent events (safe):

```bash
tail -n 20 "${ACP_AUDIT_LOG_DIR:-./audit_logs}/api_events.jsonl"
```

Do not share log contents externally without redaction review.

## Health endpoint

```bash
curl -s http://127.0.0.1:8080/health
```

Expect `{"status":"ok","mode":"local"}` or `production`. No authentication required.

## Safe demo commands

```bash
make setup
make demo
```

API example (local, auth optional):

```bash
uvicorn agent_control_plane.api:app --reload --port 8080
curl -s -X POST http://127.0.0.1:8080/run \
  -H 'Content-Type: application/json' \
  -H 'X-Correlation-ID: demo-corr-1' \
  -d '{"request_id":"demo-1","user_id":"user-1","session_id":"sess-1","tenant_id":"tenant-a","user_message":"Read my records","scenario":"safe_read","path":"protected"}'
```

Production profile requires `X-API-Key` or `Authorization: Bearer` with configured keys.

## Common failure modes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `ConfigurationError` on start | Invalid `ACP_*` combination | Read error message; fix env |
| 401 on `/run` | Missing API key | Set `X-API-Key` or disable auth for local only |
| 413 on `/run` | Body too large | Reduce payload; check `ACP_MAX_REQUEST_BODY_BYTES` |
| `adapter_failure` in audit | `disabled_external` adapter | Set `ACP_LLM_ADAPTER_MODE=simulated` |
| Policy load error | Missing or corrupt YAML | Restore `policies/default.yaml` |
| Docker pytest differs | Stale image | `docker compose build --no-cache` |

## Docker troubleshooting

| Symptom | Action |
|---------|--------|
| Cannot connect to Docker daemon | Start Docker Desktop or system service |
| pip install fails in build | Check network; rebuild with `--no-cache` |
| Tests differ from host | Image has no bind mount; rebuild after code changes |

```bash
docker compose build
docker compose run --rm app python -m pytest
```

## Policy hash mismatch response

1. Run `python scripts/validate_policy.py` for error detail.
2. If YAML change was intentional: `python scripts/validate_policy.py --write-hash`
3. Commit updated `policies/default.sha256` with policy change.
4. Never deploy with hash mismatch in CI.

## Secret scan failure response

1. Open GitHub Actions Secret scan (Gitleaks) log.
2. If finding is in `tests/` with `lab-fake` fixture, confirm allowlist in `.gitleaks.toml`.
3. If real secret: rotate credential, remove from history per org process, re-run scan.
4. Do not commit `.env` with real keys.

## Trivy failure response

1. Review CRITICAL/HIGH unfixed CVEs in image report.
2. Update base image or dependencies via Dependabot PR.
3. Re-run `make validate` after merge.
4. Document accepted risk only through organizational exception process.

## CI failure response

1. Identify failing job: lint, mypy, pytest, repo hygiene, policy integrity, bandit, pip-audit, Docker.
2. Reproduce locally: `make validate`.
3. Fix root cause; do not skip or weaken security tests.
4. Push fix; confirm all workflows green before release.

## Incident response notes

- Preserve audit JSONL before restart (see [audit-review-playbook.md](audit-review-playbook.md)).
- Use `correlation_id` from client header or `request_id` for tracing.
- Escalate cross-tenant and output-filter critical events per playbook.

## Related documents

- [audit-event-taxonomy.md](audit-event-taxonomy.md)
- [siem-export.md](siem-export.md)
- [production-hardening.md](production-hardening.md)
- [llm-adapter.md](llm-adapter.md)
