# Security Gap Assessment

Assessment date: 2026-05-17 (baseline: release v0.1.2, main through Mermaid/badge polish).

This document evaluates **gaps between the current lab and production-grade agent security**. It does not change the project scope: this remains a defensive reference implementation with simulated tools and local testing only.

## Rating summary

| Lens | Score | Notes |
|------|-------|-------|
| Public defensive lab | 10/10 | Clear doctrine, tests, CI, docs, safe scope |
| Security architecture teaching | 10/10 | Broker-centric model is well demonstrated |
| Open-source hygiene | 9.8/10 | Prompt-artifact scanner; supply-chain tooling incomplete |
| Production readiness | 7.5/10 | Intentional lab boundaries |
| Research extensibility | 8.8/10 | Strong base; deeper controls planned |

## What is already strong (implemented and tested)

| Area | Evidence |
|------|----------|
| Deny-by-default policy | `policies/default.yaml`, `tests/test_policy_engine.py` |
| Policy integrity (schema + hash) | `policy_integrity.py`, `scripts/validate_policy.py`, `tests/test_policy_integrity.py` |
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

## Gap 1: Provenance integrity (declarative only)

### Current state

Provenance is **declarative metadata** on tool calls and retrieved chunks (`source`, `trust`, `context_ids`). Policy uses it; tests prove untrusted sources cannot authorize tools. See [provenance.md](provenance.md).

### Risk

A compromised ingestion pipeline or malicious label could mark untrusted content as `internal_reviewed`. The lab does not verify who produced the metadata.

### Maturity target

Signed or hashed provenance bound to retrieval events and service identity.

### Tests needed before claiming the control

- Reject tool calls when provenance signature missing or invalid
- Reject when content hash does not match attested retrieval event
- Reject when tenant on provenance does not match request tenant
- Positive path: valid signed internal_reviewed allows only permitted tools

## Gap 2: Policy integrity (partially addressed in P0)

### Current state (after P0)

`policies/default.yaml` is validated by `policy_integrity.py` and `scripts/validate_policy.py`. Canonical SHA-256 is checked against `policies/default.sha256` in `make validate` and CI. Invariants enforce default deny, required demo tools, disabled `run_shell`, `send_email` approval, and `export_records` admin-only rules.

### Remaining risk

SHA-256 detects drift; it does not prove who changed the file. Signed policy attestation and optional `policy_hash` audit events at pipeline start remain future work.

### Maturity target (remaining)

Signed policy bundle, policy change audit event on load, runtime verification hook in `load_policy` (optional).

### Tests implemented (P0)

- `tests/test_policy_integrity.py` — schema, invariants, hash determinism, script mismatch failure

## Gap 3: Tool-output injection (under-tested)

### Current state

Doctrine and architecture state tool output is untrusted. Prompt assembly marks retrieved content as untrusted evidence. **No dedicated tests** simulate malicious content returned **from a tool execution step** influencing a later turn (tool-output-as-injection vector).

### Risk

In multi-turn agents, tool responses could carry instructions that affect later model turns if a future adapter feeds tool output back without re-filtering.

### Maturity target

Document the distrust model; add scenarios and tests for tool-returned instruction-like text, wrong-tenant data in tool results, and follow-up tool-call attempts driven by simulated tool output.

### Tests needed (examples)

- Simulated tool result contains "ignore policy" — must not bypass broker on next turn
- Tool result references foreign tenant — blocked by policy or filter
- Tool result triggers disallowed follow-up tool without approval

## Gap 4: Approval semantics (simulated checkbox)

### Current state

`AgentRequest.human_approval` is a boolean. Approval gate integrates with broker. No approval ID, approver identity, expiration, or binding to action/target hash.

### Risk

Replay or context change after approval; approver cannot see what was approved.

### Maturity target

Structured approval token: `approval_id`, `approver_id`, `expires_at`, `action_hash`, `target_hash`, one-time use, audit linkage.

### Tests needed

- Deny when approval token expired
- Deny when target or tool args changed after approval minted
- Deny on reuse of one-time approval ID
- Allow only when token matches request fingerprint

## Gap 5: Output filtering depth (pattern-based)

### Current state

`output_filter.py` blocks secret patterns, private keys, JWT-like strings, encoded blobs. Tested in `tests/test_output_filter.py`.

### Risk

Encoded, split, or low-signal leaks may evade regex-only checks.

### Maturity target

Layered filters: entropy heuristics, structured finding types, tenant-aware rules, optional allowlisted response schemas for specific tools.

### Tests needed per new rule

- Positive and negative cases; no weakening of existing pattern tests

## Gap 6: Adversarial fuzzing (deterministic suite only)

### Current state

98 deterministic pytest cases. No Hypothesis or property-based tests on schemas, targets, or policy decisions.

### Risk

Edge-case strings bypass validators.

### Maturity target

Hypothesis tests for `schemas.py`, email/tenant targets, output filter inputs, policy engine decisions (bounded examples).

## Gap 7: Supply-chain posture (baseline only)

### Current state

CI: ruff, mypy, pytest, repo hygiene, bandit, pip-audit, Docker. Actions use floating `@v4` / `@v5` tags. No Dependabot, CodeQL, gitleaks, Trivy, or SBOM in repo.

### Risk

Dependency and workflow drift; secrets in commits; container CVEs undetected in CI.

### Maturity target

Dependabot, CodeQL workflow, secret scanning, Trivy on image, SBOM artifact, pinned action SHAs, documented signed-release guidance.

## Gap 8: API hardening (demo scope)

### Current state

FastAPI demo (`api.py`): `/health`, `/run`, no auth, no rate limits. Documented as local lab only.

### Risk

Operators deploy demo without auth and expose broker to the network.

### Maturity target

`docs/production-hardening.md`: authn/z, rate limits, request size limits, CORS, TLS, network isolation, non-root container, read-only rootfs.

No requirement to implement auth in the lab unless explicitly scoped later.

## Gap 9: Simulated model (intentional)

### Current state

`agent_core.py` is scenario-driven. No live LLM API. Safe for public repo.

### Risk

Integrators unclear how to attach a real model safely.

### Maturity target

`LLMClient` protocol, `LocalFakeLLMClient`, stub `ExternalLLMClient` raising `NotImplementedError`, integration guide without API keys by default.

## Non-goals (unchanged)

- Real shell or network execution from model output
- Live exploitation or third-party testing
- Production certification claims
- Jailbreak or offensive libraries

## Related documents

- [v0.2.0-hardening-plan.md](v0.2.0-hardening-plan.md) — prioritized work packages
- [ROADMAP.md](../ROADMAP.md) — tracked items
- [threat-model.md](threat-model.md) — threat framing
