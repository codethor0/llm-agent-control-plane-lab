## Summary

**v0.2.5** adds a safe LLM adapter interface: a protocol and factory for candidate model output with simulated default behavior and a fail-closed external stub. Adapter output remains untrusted and flows through the existing output filter, schema validation, tool broker, and simulated tools.

This remains a **production-oriented defensive reference implementation**, not a drop-in production LLM service.

## What changed since v0.2.4

| Area | Change |
|------|--------|
| LLM adapter | `LLMAdapter` protocol, `SimulatedLLMAdapter`, `DisabledExternalLLMAdapter` |
| Pipeline | `_generate_model_turn()` routes model turns through the adapter |
| Config | `ACP_LLM_ADAPTER_MODE`, `ACP_ALLOW_LIVE_LLM_CALLS` (rejected if true), optional provider/model labels |
| Docs | [docs/llm-adapter.md](llm-adapter.md) — trust boundary and future integration requirements |
| Tests | **248** pytest tests (was 233 on v0.2.4) |

## P8: Safe LLM adapter interface

| Control | Implementation |
|---------|----------------|
| Default adapter | `SimulatedLLMAdapter` — offline, delegates to `agent_core.py` |
| External stub | `DisabledExternalLLMAdapter` — fail-closed `LLMAdapterError` |
| Untrusted output | Adapter returns candidate text only; broker authorizes tools |
| Live calls blocked | `ACP_ALLOW_LIVE_LLM_CALLS=true` rejected at `AppConfig.validate()` |
| No network I/O | Simulated path performs no HTTP calls to providers |
| Pipeline integration | Output filter, schema validation, and broker unchanged |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 248 passed |
| docker compose pytest | 248 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit / pip-audit | pass |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | CI, CodeQL, Secret scan, Trivy, SBOM green |

## What did not change

- Simulated tools only; **no live external tool execution**
- **No live LLM API calls** — no OpenAI, Anthropic, or other provider clients
- No provider credential handling in config
- v0.2.4 and earlier release tags unchanged

## Honest limitations

- **Not a managed production LLM service** — organizational review still required
- No live provider adapters; `disabled_external` mode fails closed
- Future live adapters require provider-specific tests, KMS/secret manager, logging review, rate limiting, and security review
- No enterprise IdP, persistent approvals, production KMS, edge rate limiting, or SIEM integration (unchanged from v0.2.4)

## Upgrade notes

- New environment variables: `ACP_LLM_ADAPTER_MODE` (default `simulated`), `ACP_ALLOW_LIVE_LLM_CALLS` (must stay `false`)
- Optional metadata labels: `ACP_LLM_PROVIDER_NAME`, `ACP_LLM_MODEL_NAME`
- See [docs/llm-adapter.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/llm-adapter.md)

## Prior releases

- [v0.2.4](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.4) — production deployment hardening
- [v0.2.3](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.3) — supply-chain hardening
- [v0.2.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.2) — property-based security coverage

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md) and [docs/llm-adapter.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/llm-adapter.md).
