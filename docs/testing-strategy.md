# Testing Strategy

## Principles

1. Tests are the specification for security behavior.
2. Every control has positive and negative cases where applicable.
3. Tests are deterministic and do not call external services.
4. Do not mock away the control under test.

## Layout (271 tests)

| File | Focus |
|------|-------|
| `test_approval_tokens.py` | Approval token binding, replay, and broker integration |
| `test_provenance_integrity.py` | Lab HMAC provenance sign/verify and strict mode |
| `test_tool_output_injection.py` | Tool output as untrusted evidence; TOOL_OUTPUT provenance denied |
| `test_policy_integrity.py` | Policy schema, invariants, canonical SHA-256 |
| `test_policy_engine.py` | Policy rules and deny reasons |
| `test_provenance.py` | Declarative provenance authorization |
| `test_tool_broker.py` | Authority boundary |
| `test_approval_gate_integration.py` | Human approval wired through broker and pipeline |
| `test_schema_validation.py` | Structure-only validation |
| `test_output_filter.py` | Layered leak prevention (patterns, entropy, tenant/destination/schema, audit metadata) |
| `test_property_*.py` | Hypothesis property-based edge cases (schemas, broker, provenance, approval, output filter, repo hygiene) |
| `test_audit_logger.py` | JSONL schema and redaction |
| `test_audit_events.py` | Pipeline audit event types |
| `test_pipeline_protected.py` | End-to-end protected path |
| `test_pipeline_vulnerable.py` | Lab vulnerable path |
| `test_security_invariants.py` | Cross-cutting invariants |
| `test_invariants.py` | Explicit security invariant coverage |
| `test_api.py` | FastAPI smoke tests |
| `test_config.py` | Production configuration validation |
| `test_api_hardening.py` | API auth, body limits, safe errors |
| `test_llm_adapter.py` | LLM adapter boundary, fail-closed external stub, pipeline integration |
| `test_audit_observability.py` | Correlation IDs, API audit safety, adapter failure audit, taxonomy coverage |
| `test_deployment_artifacts.py` | Production Compose/K8s/env examples; no real secrets; honest docs |
| `test_validate_repo.py` | Prompt-artifact hygiene scanner |

## Adding a new tool safely

1. Add policy entry in `policies/default.yaml` with explicit `enabled`, roles, and approval flags.
2. Run `python scripts/validate_policy.py --write-hash` to update `policies/default.sha256` when the canonical policy changes.
3. Add Pydantic argument schema in `schemas.py`.
4. Add simulator branch in `simulator.py` (simulation only).
5. Add agent core scenario only for deterministic tests.
6. Add policy, provenance, approval, and pipeline tests before merging.

## Running tests

```bash
make setup
make validate
```

Docker:

```bash
docker compose build
docker compose run --rm app python -m pytest
```

## CI and supply-chain tests (P6)

GitHub Actions (see [supply-chain.md](supply-chain.md)):

| Workflow | Validates |
|----------|-----------|
| CI | ruff, mypy, pytest (271), repo hygiene, policy integrity, bandit, pip-audit, Docker |
| CodeQL | Python static analysis |
| Secret scan | Gitleaks on git history (tests/ allowlist for lab-fake fixtures only) |
| Trivy | Docker image CRITICAL/HIGH (unfixed) |
| SBOM | CycloneDX JSON artifact (unsigned) |

These improve release hygiene; they do not prove absence of bugs or replace red-team review.

## Forbidden patterns

- `@pytest.mark.skip` or `xfail` on security tests
- Weakening assertions to match broken controls
- Mocking `broker_tool_request` or `evaluate_policy` in control tests
