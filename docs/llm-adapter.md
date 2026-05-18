# LLM Adapter Interface

The LLM adapter is the **candidate output boundary** between an (optional) language model provider and the external control plane. Adapters produce **untrusted** text and optional structured tool-call candidates only. They never authorize tools, call tools, or bypass policy.

## Purpose

- Isolate future provider integrations behind a single interface
- Keep the default runtime **fully simulated and offline**
- Make explicit that model output is always untrusted
- Ensure all paths still flow through output filtering, schema validation, and the tool broker

## Trust boundary

```
[LLM adapter]  -->  candidate natural_language + optional tool_call
        |
        v
[Output filter]  -->  [Schema validation]  -->  [Tool broker]  -->  [Simulated tools]
```

The adapter is **not** part of the authority boundary. The tool broker remains the authority for execution.

## Default mode: simulated

| Setting | Default |
|---------|---------|
| `ACP_LLM_ADAPTER_MODE` | `simulated` |
| `ACP_ALLOW_LIVE_LLM_CALLS` | `false` |

`SimulatedLLMAdapter` delegates to the deterministic lab agent core (`agent_core.py`). No network I/O is performed.

## External mode: disabled stub

`ACP_LLM_ADAPTER_MODE=disabled_external` selects `DisabledExternalLLMAdapter`, which **fails closed** with `LLMAdapterError`. No live provider implementation exists in this repository.

## Configuration

| Variable | Description |
|----------|-------------|
| `ACP_LLM_ADAPTER_MODE` | `simulated` or `disabled_external` |
| `ACP_ALLOW_LIVE_LLM_CALLS` | Must remain `false` (not implemented) |
| `ACP_LLM_PROVIDER_NAME` | Optional label for future providers |
| `ACP_LLM_MODEL_NAME` | Optional model label |

Validation rejects `ACP_ALLOW_LIVE_LLM_CALLS=true` because live calls are not implemented.

## Wiring

`ControlPlanePipeline` accepts an optional `llm_adapter` argument. Default: `SimulatedLLMAdapter`. The FastAPI app builds the adapter from `AppConfig` via `create_llm_adapter_from_config()`.

## Requirements for future live adapters

Any future live provider integration must:

1. Remain **opt-in** via configuration and explicit operator approval
2. Load API keys from a secret manager, never from git
3. Never log raw prompts, completions, or API keys
4. Return only `LLMAdapterResponse` (untrusted candidate output)
5. Not call tools, policy, or approval subsystems directly
6. Include provider-specific security tests and red-team review
7. Respect rate limits at the edge and provider client
8. Fail closed on provider errors without leaking credentials

## Logging restrictions

- Do not log `user_message`, retrieved chunks, or model completions at info level in production
- Do not include API keys or bearer tokens in exceptions
- Adapter errors use generic messages (`LLMAdapterError`)

## Production limitations

- P8 adds the **interface only**; no live OpenAI, Anthropic, or other API clients
- This project is not a managed production LLM service
- Organizational review is required before enabling any live provider

## Related

- [production-hardening.md](production-hardening.md)
- [architecture.md](architecture.md)
- [SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md)
