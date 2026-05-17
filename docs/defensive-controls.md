# Defensive Controls

Each control lists its **tested invariant** and primary tests. If a control is not listed here with tests, treat it as not proven.

## Deny by default

- **Invariant:** Unknown tools and default policy resolve to deny.
- **Tests:** `test_unknown_tool_denied_by_policy`, `test_missing_policy_file_denies_unknown_tools`, `test_invariant_policy_defaults_to_deny`

## Schema validation is not authorization

- **Invariant:** Valid structure does not imply allow.
- **Tests:** `test_schema_valid_does_not_imply_authorization`, `test_broker_denies_valid_schema_when_policy_denies`, `test_invariant_schema_validation_not_authorization`

## Tool broker authority boundary

- **Invariant:** Broker is the gate before simulation; policy and approval run inside the broker path.
- **Tests:** `tests/test_tool_broker.py`, `test_invariant_tool_broker_is_authority_boundary`

## Disabled tools

- **Invariant:** `run_shell` is disabled in policy.
- **Tests:** `test_run_shell_disabled_by_policy`, `test_shell_attempt_blocked_on_protected_path`

## Provenance required

- **Invariant:** Missing provenance blocks execution.
- **Tests:** `test_missing_provenance_blocks_execution`, `test_missing_provenance_blocks_tool_calls`

## Untrusted and user-derived sources

- **Invariant:** User, retrieved, web, email, and support-ticket provenance cannot authorize tool execution.
- **Tests:** `test_untrusted_retrieved_cannot_authorize_external_effect`, `test_user_generated_cannot_authorize_external_effects`, `test_injection_send_email_blocked`, `tests/test_provenance.py`

## Internal reviewed reads

- **Invariant:** `internal_reviewed` provenance may authorize safe internal reads only.
- **Tests:** `test_internal_reviewed_allows_safe_internal_read`, `test_internal_reviewed_read_succeeds`

## Human approval (approval gate)

- **Invariant:** `send_email`, external-effect, and destructive tools require `human_approval` on the request; approval does not bypass policy.
- **Tests:** `test_send_email_requires_human_approval_via_broker`, `test_export_records_requires_admin_and_approval`, `tests/test_approval_gate_integration.py`, `test_audit_approval_denied`

## Role checks

- **Invariant:** `export_records` requires `admin` role.
- **Tests:** `test_export_records_requires_admin_role`, `test_export_records_allowed_for_admin_with_approval`

## Tenant isolation

- **Invariant:** Tool target must match request tenant.
- **Tests:** `test_cross_tenant_target_denied`, `test_tenant_mismatch_blocks_execution`, `test_audit_cross_tenant_blocked`

## Output filter

- **Invariant:** Secrets, private keys, JWT-like strings, and encoded blobs are blocked outside the model.
- **Tests:** `tests/test_output_filter.py` (layered findings, entropy, tenant/destination/schema rules), `test_output_leak_blocked_before_tool_stage`, `test_invariant_output_filter_outside_model`, `test_pipeline_output_filter_audit_has_safe_metadata`

## Audit logging

- **Invariant:** Allow, block, schema failure, output filter, approval, provenance, and cross-tenant events are logged; secrets redacted.
- **Tests:** `tests/test_audit_logger.py`, `tests/test_audit_events.py`, pipeline audit tests, `test_invariant_audit_writes_for_allow_and_block`

## Simulated execution only

- **Invariant:** No real shell or external execution.
- **Tests:** `test_simulator_never_executes_real_shell`, `test_invariant_no_real_shell_from_model_output`, vulnerable path simulation tests

## Vulnerable vs protected paths

- **Invariant:** Vulnerable path labels unsafe decisions without broker; protected path blocks them.
- **Tests:** `tests/test_pipeline_vulnerable.py`, `test_invariant_protected_path_enforces_control_plane`
