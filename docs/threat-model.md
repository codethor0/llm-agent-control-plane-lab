# Threat Model

## Assets

- Tenant data (simulated records)
- Policy configuration (`policies/default.yaml`)
- Audit logs (`audit_logs/` or temp paths)
- User/session identifiers in requests

## Trust boundaries

| Inside boundary | Outside / untrusted |
|-----------------|---------------------|
| Policy engine, broker, output filter | User messages |
| Audit redaction logic | Retrieved RAG chunks |
| Simulated tool executor | Model-generated text and tool calls |

## Attacker goals

1. Execute tools without authorization (prompt injection / authority confusion)
2. Exfiltrate secrets via model output
3. Trigger external effects (email, export) without approval
4. Escalate across tenants
5. Invoke disabled tools such as `run_shell`

## Assumptions

- Attackers control user input and may influence retrieved content
- The simulated model may follow malicious instructions in retrieved text
- Policy YAML is maintained by defenders, not attackers
- Deployments use this repo only in authorized local lab environments

## Mitigations (tested)

| Threat | Control | Test area |
|--------|---------|-----------|
| Unauthorized tool call | Broker + deny-by-default policy | `tests/test_policy_engine.py`, `tests/test_tool_broker.py` |
| Schema-only bypass | Broker after schema validation | `tests/test_tool_broker.py` |
| RAG-driven external action | Untrusted provenance block | `tests/test_provenance.py`, `tests/test_policy_engine.py` |
| Missing approval | Approval gate in broker | `tests/test_approval_gate_integration.py`, `tests/test_audit_events.py` |
| Cross-tenant access | Target tenant match | `tests/test_policy_engine.py` |
| Secret leakage | Output filter + audit redaction | `tests/test_output_filter.py`, `tests/test_audit_logger.py` |
| Shell execution | `run_shell` disabled; simulator refuses | `tests/test_policy_engine.py`, `tests/test_security_invariants.py` |

## Non-goals

- Protecting against compromised policy files on disk
- Cryptographic provenance attestation
- Production-scale identity federation
- Real-world LLM jailbreak research payloads
