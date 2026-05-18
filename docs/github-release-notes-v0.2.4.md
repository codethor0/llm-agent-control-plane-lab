## Summary

**v0.2.4** adds production deployment hardening: typed configuration with fail-closed production validation, API authentication boundaries, request limits, safe error responses, container hardening, and deployment documentation.

This remains a **production-oriented defensive reference implementation**, not a drop-in production service.

## What changed since v0.2.3

| Area | Change |
|------|--------|
| Config | `AppConfig` with `local`, `test`, `production` profiles |
| API | API key auth on `/run`, body size limit, CORS restrictions, safe errors |
| Container | Non-root `appuser`, healthcheck, Compose read-only + tmpfs |
| Docs | `production-hardening.md`, `deployment-threat-model.md` |
| Tests | **233** pytest tests (was 210 on v0.2.3) |

## P7: Production deployment hardening

| Control | Implementation |
|---------|----------------|
| Production config validation | `config.py`; `AppConfig.validate()` fail-closed |
| API authentication | `X-API-Key` / `Authorization: Bearer` on `/run` when required |
| Health endpoint | `/health` unauthenticated |
| Request body limit | `MaxBodySizeMiddleware` |
| Production-safe errors | No stack traces or verbose validation payloads |
| CORS | Explicit origins; wildcard blocked in production |
| Pipeline flags | Strict provenance and approval-token requirements from config |
| Live/shell tools | Must remain disabled (validated at startup) |
| Container | Non-root user, read-only Compose profile, tmpfs for `/tmp` |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 233 passed |
| docker compose pytest | 233 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- Simulated tools only; **no live external tool execution**
- No live LLM API integration
- v0.2.3 and earlier release tags unchanged

## Honest limitations

- **Not a drop-in production service** — organizational review still required
- No enterprise IdP integration
- No persistent approval store (lab in-memory registry only)
- No production KMS for API or provenance keys
- No in-app distributed rate limiter (documented for edge infrastructure)
- No SIEM integration by default
- Branch protection is guidance until configured in GitHub

## Upgrade notes

- New environment variables: see `.env.example` (`ACP_*` prefix)
- Production profile: set `ACP_ENVIRONMENT=production` and satisfy validation before exposing the API
- Uvicorn entry: `agent_control_plane.api:app` (lazy ASGI initialization)

## Prior releases

- [v0.2.3](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.3) — supply-chain hardening
- [v0.2.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.2) — property-based security coverage
- [v0.2.1](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.1) — layered output filtering

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md) and [docs/production-hardening.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/production-hardening.md).
