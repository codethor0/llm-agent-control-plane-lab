## Summary

**v0.2.2** adds deterministic Hypothesis property-based tests that stress existing security controls with bounded, lab-safe generated inputs. No runtime behavior changes in `src/agent_control_plane/`.

This remains a **production-oriented defensive reference implementation**, not a drop-in production service.

## What changed since v0.2.1

| Area | Change |
|------|--------|
| Tests | **210** pytest tests (was 167 on v0.2.1) |
| Property tests | 43 new Hypothesis tests across 6 modules |
| Dependencies | `hypothesis` added to dev extras only |
| CI profile | `max_examples=25`, `derandomize=true` |

## P5: Property-based security coverage

| Module | Coverage |
|--------|----------|
| `test_property_schemas.py` | Unknown tools, malformed args, schema not authorization |
| `test_property_broker.py` | Deny-by-default, disabled tools, cross-tenant, non-authorizing provenance |
| `test_property_provenance_integrity.py` | HMAC sign/verify, tamper detection, signature not authorization |
| `test_property_approval_tokens.py` | Binding, reuse, expiry, field mismatch |
| `test_property_output_filter.py` | Entropy, tenant/destination/schema, redacted audit findings |
| `test_property_repo_hygiene.py` | Forbidden prompt-artifact paths vs allowed governance files |

## Validation status

| Check | Result |
|-------|--------|
| pytest | 210 passed |
| docker compose pytest | 210 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit | no issues |
| pip-audit | no known vulnerabilities |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | green |

## What did not change

- No changes to `src/agent_control_plane/` runtime logic
- Simulated tools only; no live LLM API
- No production IdP, persistent approval store, or enterprise DLP
- v0.2.1 and earlier release tags unchanged

## Honest limitations

- Property tests use **bounded examples** (`max_examples=25` in CI); not exhaustive fuzzing
- They improve edge-case coverage but **do not prove absence of bugs**
- They do **not replace** production red-team review or formal verification
- Generated fixtures use lab-fake strings only; no real secrets in tests

## Upgrade notes

- Dev install now includes Hypothesis: `pip install -e ".[dev]"`
- Local runs use the same deterministic profile as CI via `tests/conftest.py` and `pyproject.toml`

## Prior releases

- [v0.2.1](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.1) — layered output filtering, project rename
- [v0.2.0](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.0) — integrity hardening (P0-P3)
- [v0.1.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.2) — E2E verification

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
