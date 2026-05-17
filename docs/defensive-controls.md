# Defensive Controls

Each control lists its **tested invariant** and primary tests.

## Deny by default

- **Invariant:** Unknown tools and default policy resolve to deny.
- **Tests:** `test_unknown_tool_denied_by_policy`, `test_missing_policy_file_denies_unknown_tools`

## Schema validation is not authorization

- **Invariant:** Valid structure does not imply allow.
- **Tests:** `test_schema_valid_does_not_imply_authorization`, `test_broker_denies_valid_schema_when_policy_denies`

## Tool broker authority boundary

- **Invariant:** Broker is the gate before simulation.
- **Tests:** `tests/test_tool_broker.py`, `tests/test_pipeline_protected.py`

## Disabled tools

- **Invariant:** `run_shell` is disabled in policy.
- **Tests:** `test_run_shell_disabled_by_policy`, `test_shell_attempt_blocked_on_protected_path`

## Provenance required

- **Invariant:** Missing provenance blocks execution.
- **Tests:** `test_missing_provenance_blocks_execution`

## Untrusted retrieved content

- **Invariant:** Untrusted retrieved provenance cannot authorize external-effect tools.
- **Tests:** `test_untrusted_retrieved_cannot_authorize_external_effect`, `test_injection_send_email_blocked`

## Human approval

- **Invariant:** `send_email` and high-impact tools require `human_approval` on the request.
- **Tests:** `test_send_email_requires_human_approval`, `test_export_requires_admin_and_approval`

## Role checks

- **Invariant:** `export_records` requires `admin` role.
- **Tests:** `test_export_records_requires_admin_role`, `test_export_records_allowed_for_admin_with_approval`

## Tenant isolation

- **Invariant:** Tool target must match request tenant.
- **Tests:** `test_cross_tenant_target_denied`

## Output filter

- **Invariant:** Secrets, private keys, JWT-like strings, and encoded blobs are blocked outside the model.
- **Tests:** `tests/test_output_filter.py`, `test_output_leak_blocked_before_tool_stage`

## Audit logging

- **Invariant:** Allow, block, schema failure, and output filter events are logged; secrets redacted.
- **Tests:** `tests/test_audit_logger.py`, pipeline audit tests

## Simulated execution only

- **Invariant:** No real shell or external execution.
- **Tests:** `test_simulator_never_executes_real_shell`, vulnerable path simulation tests

## Vulnerable vs protected paths

- **Invariant:** Vulnerable path labels unsafe decisions without broker; protected path blocks them.
- **Tests:** `tests/test_pipeline_vulnerable.py`
