## Summary

**v0.2.1** ships P4 layered output filtering and renames the public project to **llm-agent-control-plane** (repository display name). The Python install package name remains `llm-agent-control-plane-lab` for import stability.

This remains a **local, simulated** reference implementation. Simulated tools only; no live LLM API by default; not a drop-in production service.

## What changed since v0.2.0

| Area | Change |
|------|--------|
| Tests | **167** pytest tests (was 149 on v0.2.0) |
| Output filter | Layered checks beyond pattern matching |
| Project name | GitHub repository renamed to `llm-agent-control-plane` |
| Docs | Positioning updated; honest production boundary |

## P4: Layered output filtering

- Structured `OutputFinding` results with redacted samples only
- High-entropy string heuristic (documented Shannon threshold)
- Existing secret, private key, JWT, and encoded-blob detection preserved
- Tenant-aware blocking via `tenant_id:` markers
- Destination-aware rules (`internal_display`, `audit_log`, `external_email`, `external_export`, `webhook`)
- Source sensitivity propagation from retrieved chunks and tool output segments
- Strict response schema mode with sensitive key denial
- Audit JSONL includes output-filter decision metadata (redacted findings only)

Approval is not authorization. Policy, provenance, schema, and broker checks still apply first.

## Security architecture (v0.2.1)

```
Policy integrity
  -> Tool-output distrust
  -> Provenance integrity (strict mode optional)
  -> Approval token binding
  -> Layered output filtering
```

The model can ask. The broker decides.

## Validation status

| Check | Result |
|-------|--------|
| pytest | 167 passed |
| docker compose pytest | 167 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit | no issues |
| pip-audit | no known vulnerabilities |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | green |

## Repository rename

- **New URL:** https://github.com/codethor0/llm-agent-control-plane
- GitHub redirects the former `llm-agent-control-plane-lab` URL automatically
- Python package/import name unchanged: `agent_control_plane` (pip name `llm-agent-control-plane-lab`)

## What did not change

- Simulated tools only; no real shell, network, or external execution from model output
- No live LLM API wiring by default
- No production identity provider, approval UI, or distributed token store
- No production PKI or HSM-backed signing
- v0.2.0 tag and release history unchanged

## Honest limitations

- Output filtering uses lab heuristics; not enterprise DLP
- Pipeline pre-broker filtering defaults to `internal_display` destination context
- Production systems still need identity, persistence, key management, observability, and deployment hardening (see roadmap P5-P7)

See [docs/security-gap-assessment.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/security-gap-assessment.md).

## Upgrade notes

- Clone or remote URL: `https://github.com/codethor0/llm-agent-control-plane.git`
- Optional layered filtering: `filter_output(text, OutputFilterContext(...))` and `build_filter_context_from_request(request)`
- `filter_model_output(text)` remains backward compatible

## Prior releases

- [v0.2.0](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.2.0) — integrity hardening (P0-P3)
- [v0.1.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.2) — E2E verification and hygiene scanner fix
- [v0.1.1](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.1) — documentation and architecture assets
- [v0.1.0](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.0) — initial public release

## Safe use

Authorized local testing only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
