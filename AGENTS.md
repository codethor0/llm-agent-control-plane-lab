# Agent Instructions

Read `PROJECT_DOCTRINE.md` before any change. Follow `.cursor/rules/` in this repository.

## Workflow

1. **Before code:** confirm invariants, identify tests for each control.
2. **While coding:** smallest correct change; tests with every control; security decisions in broker and policy engine only.
3. **After code:** run `make validate` and `make demo`; fix all failures without weakening tests.

## Non-negotiables

- Deny by default; no model-trusted authorization.
- Schema validation is not authorization.
- Simulated tools only; no real shell, network, or credentials.
- Every security invariant has positive and negative tests.
- No emojis in code, docs, or commits.
- No TODOs in core logic; no placeholder security controls.

## Key modules

| Module | Responsibility |
|--------|----------------|
| `prompt.py` | Assemble prompts; never grant authority |
| `agent_core.py` | Simulated model; untrusted output |
| `schema_validation.py` | Structure only; not authorization |
| `tool_broker.py` | Authority boundary |
| `policy_engine.py` | Deterministic allow/deny |
| `output_filter.py` | Block leaks outside model |
| `audit_logger.py` | JSONL with redaction |
| `approval_gate.py` | Human approval for high-risk actions |
| `simulator.py` | Safe simulated tool execution |
| `pipeline.py` | Orchestration; vulnerable vs protected paths |

## Documentation

Update `docs/` when architecture or controls change. Tests are the specification for security behavior.
