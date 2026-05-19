# Approval Workflow Guidance

**Status:** Lab model implemented; **persistent enterprise approval store is not implemented**.

## What exists today (lab)

| Feature | Implementation | Tests |
|---------|----------------|-------|
| Human approval flag | `AgentRequest.human_approval` + `approval_gate.py` | `tests/test_approval_gate_integration.py` |
| Approval tokens | `approval_tokens.py` in-memory registry | `tests/test_approval_tokens.py` |
| Broker requirement | `ACP_REQUIRE_APPROVAL_TOKEN` | broker and integration tests |
| Binding fields | Token ID, expiry, action hash, target hash, tenant | `tests/test_approval_tokens.py` |

Characteristics of the lab registry:

- **In-memory** — lost on process restart
- **One-time use** — replay blocked in tests
- **No approver IdP identity** — approver is not cryptographically bound to corporate identity
- **No workflow UI** — tokens are passed in API requests for demonstration

## Future persistent approval store

Enterprise deployments should use a **durable store** (database or workflow service) owned by the application team, with:

| Requirement | Rationale |
|-------------|-----------|
| Approver identity | Tie approval to corporate `user_id` from IdP |
| Expiration | Limit window for high-impact actions |
| One-time use | Prevent replay after execution |
| Action hash | Bind approval to specific tool + arguments |
| Target hash | Bind approval to resource identifiers |
| Tenant binding | Prevent cross-tenant approval reuse |
| Risk level | Map policy tool risk to approval tier |
| Audit linkage | Store `approval_id` on allow/deny audit events |
| Revocation | Admin can invalidate pending approvals |

## Approver identity

Record who approved (workforce ID), when, through which channel (ticketing system, mobile push), and the policy version in effect. The lab does not persist approver records.

## Expiration

Default short TTL for external and destructive tools (organizational policy). Lab tokens support expiry fields; enforcement is tested in `tests/test_approval_tokens.py`.

## One-time use and hashes

The lab computes hashes over canonical tool-call payloads. Production should use the same binding principles so an approval for `send_email` cannot authorize `export_records`.

## Audit linkage

Every allow/deny after approval checks should include:

- `approval_id` or token ID (non-secret identifier)
- `correlation_id`
- Tool name and stage (`tool_broker`, `approval_gate`)

## Revocation

Operators need APIs or admin tools to revoke pending approvals on compromise or policy change. **Not implemented** in this repository.

## Failure modes

| Failure | Impact |
|---------|--------|
| Shared approval token | Wrong actor executes action |
| No persistence | Restart clears approvals; race in multi-instance |
| Missing approver audit | Cannot prove who approved in incident review |
| Approval without broker | Approval is not authorization; policy still applies |

## Required tests for future implementation

Before claiming persistent approvals:

- Positive: valid stored approval allows bound action once
- Negative: expired, revoked, wrong tenant, wrong action hash denied
- Negative: replay after use denied
- Audit: approval granted/denied events with approver ID redaction rules
- Multi-instance: store consistency (integration tests against real DB test container)

## Related docs

- [enterprise-integration-plan.md](enterprise-integration-plan.md)
- [audit-review-playbook.md](audit-review-playbook.md)
- [production-hardening.md](production-hardening.md)
