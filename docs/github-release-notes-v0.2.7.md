## Summary

**v0.2.7** adds a deployment reference profile: production-oriented Compose settings, Kubernetes reference manifests, Helm guidance (no bundled chart), deployment boundaries, and a deployment checklist with artifact tests.

This remains a **production-oriented defensive reference implementation**, not a managed production platform.

## What changed since v0.2.6

| Area | Change |
|------|--------|
| Compose | `docker-compose.production.yml` — auth required, read-only rootfs, audit volume, localhost bind |
| Environment | `.env.production.example`, `deploy/examples/fake-api-keys.txt` (lab-fake only) |
| Kubernetes | `deploy/kubernetes/` reference manifests (labeled reference-only) |
| Docs | [deployment-boundaries.md](deployment-boundaries.md), [deployment-checklist.md](deployment-checklist.md), [helm-guidance.md](helm-guidance.md) |
| Tests | **271** pytest tests (was 260 on v0.2.6) |

## P10: Deployment reference profile

| Control | Implementation |
|---------|----------------|
| Production Compose | Non-root image, `read_only`, tmpfs, uvicorn API, fake API key mount |
| Production env example | `ACP_REQUIRE_API_AUTH=true`, live LLM/shell disabled |
| K8s reference | `runAsNonRoot`, dropped capabilities, probes on `/health`, NetworkPolicy |
| Helm | Guidance only; no chart in repository |
| Boundaries doc | App vs container vs CI vs operator responsibilities |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 271 passed |
| docker compose pytest | 271 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- Simulated tools only; **no live external tool execution**
- **No live LLM API calls**
- **No bundled Helm chart**, Terraform modules, or managed SIEM connector
- v0.2.6 and earlier release tags unchanged

## Honest limitations

- **Not a certified Kubernetes deployment** or managed production service
- **No Terraform**, enterprise IdP, production KMS, or persistent approval store in repo
- **No managed SIEM connector** — JSONL forwarding is operator-owned
- Operators own **TLS**, **rate limiting**, **secret rotation**, **deployment review**, and **incident response**
- Reference manifests require platform team review before production use

## Upgrade notes

- Review [docs/deployment-checklist.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/deployment-checklist.md) before network exposure
- Local reference: `docker compose -f docker-compose.production.yml up --build`
- Kubernetes: see [deploy/kubernetes/README.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/deploy/kubernetes/README.md)

## Prior releases

- [v0.2.6](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.6) — observability and audit review
- [v0.2.5](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.5) — safe LLM adapter interface
- [v0.2.4](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.4) — production deployment hardening

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md) and [docs/deployment-boundaries.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/deployment-boundaries.md).
