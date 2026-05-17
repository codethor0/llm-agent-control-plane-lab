## Summary

**v0.2.0** delivers the minimum integrity hardening bar for the defensive control plane lab: policy drift detection, lab HMAC provenance verification, dedicated tool-output injection tests, and approval tokens bound to exact tool actions.

The project remains a **local, simulated** reference implementation. Simulated tools only; no live LLM API by default; no production identity provider or PKI.

## What changed since v0.1.2

| Area | Change |
|------|--------|
| Tests | **149** pytest tests (was 84 on v0.1.2) |
| Policy | Schema validation, security invariants, canonical SHA-256 hash (`policies/default.sha256`), CI via `make policy-integrity` |
| Provenance | Lab HMAC-SHA256 over canonical provenance JSON; optional strict mode on broker and pipeline |
| Tool output | `ToolOutputSegment`, `ProvenanceSource.TOOL_OUTPUT`; 13 dedicated injection tests |
| Approval | `ApprovalToken` with action fingerprint, expiration, one-time use; legacy `human_approval` boolean retained |
| Docs | v0.2.0 hardening plan, security gap assessment, expanded provenance documentation |
| README | Mermaid diagrams, badges, 149-test count |

## P0: Policy integrity

- `src/agent_control_plane/policy_integrity.py` — validates `policies/default.yaml` structure and lab security invariants
- `scripts/validate_policy.py` — compares canonical policy SHA-256 to `policies/default.sha256`
- `make policy-integrity` wired into `make validate` and GitHub Actions
- Enforces default deny, disabled `run_shell`, `send_email` approval, `export_records` admin-only rules

SHA-256 detects policy drift in CI; it does not prove who changed the file.

## P1: Lab HMAC provenance (strict mode)

- `src/agent_control_plane/provenance_integrity.py` — sign and verify provenance metadata with a **lab-only** fake HMAC key
- Optional fields on `Provenance`: `tenant_id`, `chunk_id`, `content_hash`, `signature`
- `require_provenance_signature=True` on broker and pipeline fails closed on missing or tampered signatures
- Default pipeline and demo remain declarative (signatures not required unless strict mode is enabled)

Signature verification is integrity-only; it is not authorization.

## P2: Tool-output injection coverage

- Prior tool output is ingested as **untrusted evidence** in prompt assembly (`may_trigger_tool_use=false`)
- `TOOL_OUTPUT` provenance source cannot authorize tools
- Protected pipeline scenarios and broker tests for instruction-like content, secrets, cross-tenant targets, and follow-up calls

Coverage is on simulated paths; production integrations must classify tool output at ingestion.

## P3: Approval token model

- `src/agent_control_plane/approval_tokens.py` — tokens bound to user, tenant, tool, target, action, risk, context IDs, and provenance fingerprint
- One-time use registry, expiration checks, mismatch denial
- Audit JSONL includes safe approval metadata (no signing keys or raw secrets)
- `require_approval_token=True` optional on broker and pipeline; `human_approval=True` still works when tokens are not required

Approval is not authorization. Policy, provenance, schema, and broker checks still apply first.

## Security architecture (v0.2.0)

```
Policy integrity
  -> Tool-output distrust
  -> Provenance integrity (strict mode optional)
  -> Approval token binding
```

The model can ask. The broker decides.

## Validation status

| Check | Result |
|-------|--------|
| pytest | 149 passed |
| docker compose pytest | 149 passed |
| ruff / mypy | pass |
| `scripts/validate_repo.py` | pass |
| `scripts/validate_policy.py` | pass |
| bandit | no issues |
| pip-audit | no known vulnerabilities |
| `make demo` | 7 scenarios OK |
| GitHub Actions on `main` | green |

Validated on commit ancestry through `9e5209f` (minimum bar documentation) and implementation commits `f5563d9`, `fd55fe0`, `fbe810d`, `0c3fdf7`.

## What did not change

- Simulated tools only; no real shell, network, or external execution from model output
- No live LLM API wiring by default
- No production identity provider, approval UI, or distributed token store
- No production PKI or HSM-backed signing
- Default pipeline does not require provenance signatures or approval tokens

## Known limitations

- Policy hash and HMAC provenance use lab-grade checks, not enterprise key management
- Approval one-time registry is in-process only
- Output filtering remains pattern-based (P4 planned)
- No Hypothesis fuzz suite yet (P5 planned)
- Supply-chain tooling beyond bandit/pip-audit not yet in CI (P6 planned)

See [docs/security-gap-assessment.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/docs/security-gap-assessment.md).

## Upgrade notes

- If you forked policy YAML, run `python scripts/validate_policy.py --write-hash` after intentional policy edits
- Strict provenance mode: pass `require_provenance_signature=True` to `ControlPlanePipeline` or `broker_tool_request`
- Strict approval mode: pass `require_approval_token=True` and supply `ApprovalToken` via `create_approval_token()`
- Existing tests using `human_approval=True` without tokens continue to work

## Next roadmap items

| Priority | Item |
|----------|------|
| P4 | Output filter layers (entropy, tenant-aware rules) |
| P5 | Hypothesis fuzz tests |
| P6 | Supply-chain tooling (Dependabot, CodeQL, gitleaks, Trivy, SBOM) |
| P7 | Production hardening documentation |
| P8 | LLM adapter interface (no live API by default) |

See [ROADMAP.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/ROADMAP.md).

## Prior releases

- [v0.1.2](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.2) — E2E verification and hygiene scanner fix
- [v0.1.1](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.1) — documentation and architecture assets
- [v0.1.0](https://github.com/codethor0/llm-agent-control-plane/releases/tag/v0.1.0) — initial public release

## Safe use

Authorized local lab use only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane/blob/main/SECURITY.md).
