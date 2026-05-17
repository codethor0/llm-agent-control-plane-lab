## Summary

First public release of a defensive reference lab that demonstrates an external control plane around a **simulated** tool-connected LLM agent.

**Core idea:** The model can ask. The broker decides.

## What this release does

- End-to-end pipeline: untrusted input, prompt assembly, simulated agent core, output filter, schema validation, tool broker, policy engine, approval gate, simulated tools, JSONL audit logging
- Deny-by-default policy with provenance and role checks
- Protected path (full control plane) and vulnerable path (labeled unsafe simulation only)
- FastAPI local API and CLI demo (`make demo`)
- 83 automated tests mapped to [defensive controls](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/defensive-controls.md)
- Prompt-artifact hygiene scanner (`scripts/validate_repo.py`) in `make validate` and CI

## What this release does not do

- Call production LLM APIs by default
- Execute real shell commands, send email, or scan networks
- Provide exploit chains, jailbreak libraries, or offensive tooling
- Certify production deployments or guarantee universal LLM safety

## Security controls (tested)

- Model output is untrusted; free-form text is not executable
- Schema validation is not authorization
- Tool broker is the authority boundary
- Untrusted retrieved/user/web/email context cannot authorize tools
- External and destructive actions require human approval
- `run_shell` disabled in policy
- Output filtering outside the model (secrets, keys, JWT-like tokens, encoded blobs)
- Audit events with redaction for allow, block, schema failure, and filter failure
- Prompt artifacts blocked from the repository

## Validation results

Validated on Python 3.12 with:

| Check | Result |
|-------|--------|
| pytest | 83 passed |
| ruff | pass |
| mypy | pass |
| bandit | pass |
| pip-audit | no known vulnerabilities |
| `scripts/validate_repo.py` | pass |
| docker compose build | pass |
| docker compose run --rm app python -m pytest | 83 passed |
| make demo | pass |

## Safe use

Use only in **authorized local lab** environments. Do not point this project at production systems, real customer data, or third-party targets. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).

## Known limitations

- Simulated model only (scenario-driven, no live LLM API)
- Provenance is declarative metadata, not signed attestation ([provenance.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/provenance.md))
- Policy file integrity on disk is assumed
- Multi-tenant isolation is demonstration-level, not production-grade

## Upgrade and future work

See [ROADMAP.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/ROADMAP.md).
