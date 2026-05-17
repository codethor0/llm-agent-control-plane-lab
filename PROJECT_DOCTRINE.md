# Project Doctrine

Repository: **llm-agent-control-plane-lab**

This document is the authoritative engineering doctrine for humans and AI agents working in this repository. Cursor rules in `.cursor/rules/` mirror and enforce these requirements.

## Core purpose

Build a defensive lab and proof-of-concept that shows how to secure LLM agents with an **external control plane**.

Demonstrated flow:

1. Untrusted input
2. Prompt assembly
3. Simulated LLM agent core
4. Schema validation
5. Tool broker
6. Policy engine
7. Output filter
8. Audit logger
9. Human approval gate
10. Safe simulated tool execution

**Core security idea:** The model can ask. The broker decides.

## Security philosophy

1. Security by design.
2. Deny by default.
3. Least privilege by default.
4. Deterministic security controls outside the model.
5. No model output is trusted.
6. Schema validation is not authorization.
7. Authorization happens in the tool broker and policy engine.
8. Untrusted retrieved content cannot authorize tools.
9. Prompt injection is authority confusion.
10. Output filtering happens outside the model.
11. Human approval for external, destructive, financial, customer-impacting, or permission-changing actions.
12. All tool execution is simulated unless explicitly designed as a safe local test.
13. No real shell execution from model output.
14. No real network scanning, credential access, exploitation, or third-party target testing.
15. No unsafe payloads, malware, exploit chains, or reusable jailbreak prompts.
16. Every security claim must be backed by tests.
17. If a control is not tested, it does not exist.

## Mandatory security invariants

| # | Invariant |
|---|-----------|
| 1 | Model output is always untrusted |
| 2 | Free-form model text is never executable |
| 3 | Schema validation is not authorization |
| 4 | Tool broker is the authority boundary |
| 5 | Policy defaults to deny |
| 6 | Unknown tools are denied |
| 7 | Disabled tools are denied |
| 8 | Missing provenance blocks tool execution |
| 9 | Untrusted retrieved content cannot authorize external effects |
| 10 | External effects require human approval |
| 11 | Destructive actions require human approval |
| 12 | `run_shell` is disabled |
| 13 | `send_email` requires human approval |
| 14 | `export_records` requires admin role and human approval |
| 15 | Cross-tenant context is blocked |
| 16 | Output filtering happens outside the model |
| 17 | Output containing secrets is blocked |
| 18 | Output containing private keys is blocked |
| 19 | Output containing JWT-like strings is blocked |
| 20 | Output containing encoded blobs is blocked |
| 21 | Audit events for allowed decisions |
| 22 | Audit events for blocked decisions |
| 23 | Audit events for schema failures |
| 24 | Audit events for output filter failures |
| 25 | No raw secrets in logs |
| 26 | No real external tools execute |
| 27 | No real shell commands from model output |
| 28 | No third-party network targets |
| 29 | Vulnerable path is simulation only |
| 30 | Protected path enforces the full control plane |

## Stack

- Python 3.12
- FastAPI, Pydantic v2, PyYAML
- pytest, ruff, mypy, bandit, pip-audit
- Docker, Docker Compose, GitHub Actions
- JSONL audit events

## Validation commands

```bash
make validate
make demo
docker compose build
docker compose run --rm app python -m pytest
```

## Absolute rule

Do not optimize for speed or appearance over correctness and security. Do not weaken tests to pass CI. Do not claim success until the repo builds, tests, validates, and demonstrates the control plane end-to-end.
