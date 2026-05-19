# Security Gap Assessment

Assessment date: 2026-05-17 (baseline: release v0.1.2, main through Mermaid/badge polish).

This document evaluates **gaps between the current lab and production-grade agent security**. It does not change the project scope: this remains a defensive reference implementation with simulated tools and local testing only.

## Rating summary

| Lens | Score | Notes |
|------|-------|-------|
| Public defensive lab | 10/10 | Clear doctrine, tests, CI, docs, safe scope |
| Security architecture teaching | 10/10 | Broker-centric model is well demonstrated |
| Open-source hygiene | 9.5/10 | Prompt-artifact scanner; CodeQL, Gitleaks, Trivy, SBOM, Dependabot (P6) |
| Production readiness | 7.5/10 | Intentional lab boundaries |
| Research extensibility | 8.8/10 | Strong base; deeper controls planned |

## What is already strong (implemented and tested)

| Area | Evidence |
|------|----------|
| Deny-by-default policy | `policies/default.yaml`, `tests/test_policy_engine.py` |
| Policy integrity (schema + hash) | `policy_integrity.py`, `scripts/validate_policy.py`, `tests/test_policy_integrity.py` |
| Provenance integrity (lab HMAC, strict mode) | `provenance_integrity.py`, `tests/test_provenance_integrity.py` |
| Approval token binding (lab) | `approval_tokens.py`, `tests/test_approval_tokens.py` |
| Tool broker authority | `tool_broker.py`, `tests/test_tool_broker.py`, `test_invariant_tool_broker_is_authority_boundary` |
| Schema is not authorization | `tests/test_schema_validation.py`, `test_invariant_schema_validation_not_authorization` |
| Provenance rules (declarative) | `provenance.py`, `tests/test_provenance.py` |
| Human approval gate (boolean flag) | `approval_gate.py`, `tests/test_approval_gate_integration.py` |
| Output filter (pattern-based) | `output_filter.py`, `tests/test_output_filter.py` |
| Cross-tenant checks | `test_cross_tenant_target_denied`, `test_tenant_mismatch_blocks_execution` |
| Disabled `run_shell` | `test_run_shell_disabled_by_policy` |
| Audit logging with redaction | `tests/test_audit_logger.py`, `tests/test_audit_events.py` |
| Prompt-artifact hygiene | `scripts/validate_repo.py`, `tests/test_validate_repo.py` (9 tests) |
| Vulnerable vs protected paths | `tests/test_pipeline_vulnerable.py`, `tests/test_pipeline_protected.py` |
| Supply-chain baseline | Bandit, pip-audit, Docker pytest in `make validate` and CI |

See [SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md) and [defensive-controls.md](defensive-controls.md).

## Gap 1: Provenance integrity (partially addressed in P1)

### Current state (after P1)

Lab HMAC-SHA256 over canonical provenance JSON in `provenance_integrity.py`. Strict broker/pipeline mode requires valid signatures; default mode remains declarative. Optional `content_hash` on `Provenance`. See [provenance.md](provenance.md).

### Remaining risk

Lab fake key is not production key management. Default pipeline does not require signatures at runtime. No service identity or attested retrieval events.

### Honest claim

HMAC mode detects metadata tampering in this reference implementation. It is not full production attestation.

### Tests implemented (P1)

- `tests/test_provenance_integrity.py` — sign/verify, tamper detection, strict pipeline, broker not bypassed

## Gap 2: Policy integrity (partially addressed in P0)

### Current state (after P0)

`policies/default.yaml` is validated by `policy_integrity.py` and `scripts/validate_policy.py`. Canonical SHA-256 is checked against `policies/default.sha256` in `make validate` and CI. Invariants enforce default deny, required demo tools, disabled `run_shell`, `send_email` approval, and `export_records` admin-only rules.

### Remaining risk

SHA-256 detects drift; it does not prove who changed the file. Signed policy attestation and optional `policy_hash` audit events at pipeline start remain future work.

### Maturity target (remaining)

Signed policy bundle, policy change audit event on load, runtime verification hook in `load_policy` (optional).

### Tests implemented (P0)

- `tests/test_policy_integrity.py` — schema, invariants, hash determinism, script mismatch failure

## Gap 3: Tool-output injection (partially addressed in P2)

### Current state (after P2)

`ToolOutputSegment` is ingested as untrusted prompt evidence (`may_trigger_tool_use=false`). `ProvenanceSource.TOOL_OUTPUT` cannot authorize tools. Dedicated tests in `tests/test_tool_output_injection.py` cover policy, broker, output filter, prompt assembly, and protected pipeline scenarios.

### Remaining risk

Coverage is simulated single-turn and test-harness multi-turn only. Production integrations must classify tool output at ingestion and never attach `TOOL_OUTPUT` provenance to authorize external effects.

### Honest claim

Tool-output injection is tested on simulated paths. This does not prove all production tool integrations are safe.

## Gap 4: Approval semantics (partially addressed in P3)

### Current state (after P3)

`ApprovalToken` model with action fingerprint, expiration, one-time use, and broker verification. Legacy `human_approval` boolean still supported when no token is supplied. Audit events include safe approval metadata. See `approval_tokens.py` and `tests/test_approval_tokens.py`.

### Remaining risk

Lab in-memory one-time registry only; no production identity provider, approval UI, or distributed token store.

### Honest claim

Approval tokens are lab-mode binding. Production systems need identity, persistence, replay protection, and audit review workflows.

## Gap 5: Output filtering depth (layered lab filters)

### Current state

`output_filter.py` applies layered checks: secret patterns, private keys, JWT-like strings, encoded blobs, high-entropy tokens, cross-tenant markers, destination-aware rules, source sensitivity propagation, and optional strict response schemas. Structured `OutputFinding` results with redacted samples. Tested in `tests/test_output_filter.py` (23 tests).

### Risk

Advanced encoding, steganography, or enterprise DLP evasion are out of scope for the lab.

### Maturity target

Production deployments need enterprise DLP, classification services, egress controls, and monitoring beyond pattern/heuristic filters.

### Tests needed per new rule

- Positive and negative cases; no weakening of existing pattern tests (maintained in P4)

## Gap 6: Adversarial fuzzing (property-based lab coverage)

### Current state

210 pytest cases including Hypothesis property tests (`tests/test_property_*.py`) for schemas, broker decisions, provenance HMAC integrity, approval tokens, output filter layers, and repo hygiene. CI profile uses `max_examples=25`, `derandomize=true`.

### Risk

Property tests increase edge-case coverage but do not prove absence of bugs or replace production red-team review.

### Maturity target

Expand bounded generation for policy fixtures and deployment profiles; optional separate long-run profile locally (not required in CI).

## Gap 7: Supply-chain posture (baseline only)

### Current state

CI: ruff, mypy, pytest (210), repo hygiene, bandit, pip-audit, Docker. P6 adds CodeQL, Gitleaks, Trivy, SBOM workflows and Dependabot config. Actions pinned to major versions or explicit third-party tags (see [supply-chain.md](supply-chain.md)).

### Risk

Residual dependency/CVE drift between scans; secrets outside git history; SBOM unsigned; branch protection not enforced unless configured in GitHub.

### Maturity target

Maintain green supply-chain workflows; enable branch protection per [branch-protection.md](branch-protection.md); optional signed tags; SHA-pinned Actions via Dependabot review.

## Gap 8: API hardening (demo scope)

### Current state

FastAPI demo (`api.py`): `/health`, `/run`; production profile requires API auth, explicit CORS, request size limits, and safe errors (`config.py`, `tests/test_api_hardening.py`). Local mode remains auth-free for lab use. Rate limiting documented at edge only.

### Risk

Operators may deploy with `ACP_ENVIRONMENT=local` on a network-facing host or skip edge rate limits.

### Maturity target

Enterprise IdP integration, per-tenant rate limits in infrastructure, and persistent approval store (P7 docs + config; not full production service).

## Gap 10: Observability and SIEM integration (partial — P9)

### Current state

Audit JSONL includes `correlation_id`, event taxonomy, SIEM export documentation, review playbooks, and operator runbooks. API boundary events (`api_auth_failure`, `request_body_limit_blocked`) and `adapter_failure` are audited. Tests in `tests/test_audit_observability.py`.

### Risk

Operators may assume bundled SIEM integration or tamper-evident centralized logging exists.

### Maturity target

OpenTelemetry traces, signed log shipping, managed SIEM connectors, and production alert runbooks owned by the deploying organization.

## Gap 9: Live LLM provider integration (partial — P8)

### Current state

`llm_adapter.py` defines `LLMAdapter`, `SimulatedLLMAdapter` (wraps `agent_core.py`), and `DisabledExternalLLMAdapter` (fail-closed). Pipeline routes model turns through the adapter; output still passes output filter, schema validation, and broker. No live API client. `ACP_ALLOW_LIVE_LLM_CALLS=true` is rejected at config validation.

### Risk

Future live adapters could bypass controls if implemented incorrectly outside this pattern.

### Maturity target

Provider-specific live adapters with isolated tests, secret manager for API keys, logging review, rate limiting, and security review before enabling network calls.

## Non-goals (unchanged)

- Real shell or network execution from model output
- Live exploitation or third-party testing
- Production certification claims
- Jailbreak or offensive libraries

## Related documents

- [v0.2.0-hardening-plan.md](v0.2.0-hardening-plan.md) — prioritized work packages
- [ROADMAP.md](../ROADMAP.md) — tracked items
- [threat-model.md](threat-model.md) — threat framing
