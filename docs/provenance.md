# Provenance Model

## Current behavior

Tool calls carry **provenance metadata** (`source`, `trust`, `context_ids`, and optional `tenant_id`, `chunk_id`, `content_hash`, `signature`). The policy engine and `provenance.py` use this metadata to decide whether a source may support a tool request.

By default, provenance is **declarative**. A simulated model (or attacker controlling prompts) can lie about fields unless strict HMAC mode is enabled.

## Source rules (tested)

| Source | May authorize tool execution |
|--------|----------------------------|
| `model`, `system` | Yes, when `trust=trusted` and policy plus approval allow |
| `internal_reviewed` | Yes for safe internal reads only (no external or destructive tools) |
| `user`, `retrieved`, `tool_output`, `external`, `web`, `email`, `support_ticket` | No (evidence only) |

Untrusted trust level always denies authorization.

## Lab HMAC integrity mode (P1)

`provenance_integrity.py` provides **lab-only** HMAC-SHA256 signing and verification over canonical provenance JSON.

| Property | Detail |
|----------|--------|
| Purpose | Detect metadata tampering in tests and strict pipeline mode |
| Key | `LAB_DEMO_HMAC_KEY` — fake constant for demonstrations only |
| Not | Production attestation, service identity, or key rotation |

### Strict verification

When `require_provenance_signature=True` on `broker_tool_request` or `ControlPlanePipeline`:

- Missing signature → `provenance_signature_missing`
- Invalid signature → `provenance_signature_invalid`
- Valid signature → existing broker policy, provenance, and approval checks still apply

**Signature verification is not authorization.** It only shows metadata was not changed after signing in this lab model.

### Content hash

`compute_content_hash()` returns SHA-256 hex of UTF-8 content. Tests use harmless sample strings. Do not log raw sensitive content.

### Default (non-strict) mode

Existing scenarios and tests continue without signatures. Declarative provenance rules are unchanged.

## Production guidance

Production deployments should add:

- Real key management and service identity
- Signed attestations bound to retrieval events
- Out-of-band human review queues with short-lived approval tokens
- Workload identity (SPIFFE, TPM, cloud instance identity) for broker-side verification

Until then, treat unsigned provenance as **hints for deterministic policy**, not proof.
