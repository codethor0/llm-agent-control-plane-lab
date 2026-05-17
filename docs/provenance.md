# Provenance Model

## Current behavior

Tool calls carry **declarative provenance metadata** (`source`, `trust`, `context_ids`). The policy engine and `provenance.py` use this metadata to decide whether a source may support a tool request.

This is **not** cryptographic attestation. A simulated model (or attacker controlling prompts) can lie about provenance fields.

## Source rules (tested)

| Source | May authorize tool execution |
|--------|----------------------------|
| `model`, `system` | Yes, when `trust=trusted` and policy plus approval allow |
| `internal_reviewed` | Yes for safe internal reads only (no external or destructive tools) |
| `user`, `retrieved`, `external`, `web`, `email`, `support_ticket` | No (evidence only) |

Untrusted trust level always denies authorization.

## Future work

Production deployments should add one or more of:

- Signed provenance attestations bound to service identity
- Out-of-band human review queues that mint short-lived approval tokens
- Hardware or workload identity (SPIFFE, TPM, cloud instance identity) for broker-side verification

Until then, treat provenance as **hints for deterministic policy**, not proof.
