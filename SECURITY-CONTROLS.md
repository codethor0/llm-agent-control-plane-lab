# Security Controls Matrix

Quick audit map for the defensive control plane reference implementation. **If a control is not backed by tests, it does not exist** (see [docs/defensive-controls.md](docs/defensive-controls.md)).

This project is a **local, simulated** reference implementation. It is not certified for production deployments.

## Matrix

| Control | Threat addressed | Implementation | Tests | Status | Known limitation |
|---------|------------------|----------------|-------|--------|------------------|
| Deny-by-default policy | Unauthorized tool use; privilege escalation via unknown tools | `policies/default.yaml` (`default: deny`); `policy_engine.py` | `test_policy_defaults_to_deny_for_unknown_tool`, `test_missing_policy_file_denies_unknown_tools`, `test_invariant_policy_defaults_to_deny` | Implemented, tested | Runtime loads YAML; enforcement depends on policy content |
| Policy integrity (schema + hash) | Accidental or malicious policy drift; weakened tool rules | `policy_integrity.py`; `scripts/validate_policy.py`; `policies/default.sha256`; `make policy-integrity`; CI | `tests/test_policy_integrity.py`, `test_default_policy_passes_integrity`, `test_hash_mismatch_fails_validation_script` | Implemented, tested | SHA-256 detects drift only; does not prove who changed the file; not signed attestation |
| Schema validation | Malformed or ambiguous tool-call payloads | `schemas.py`; pipeline validates before broker | `tests/test_schema_validation.py`, `test_schema_valid_does_not_imply_authorization`, `test_invariant_schema_validation_not_authorization` | Implemented, tested | Structure only; does not authorize execution |
| Tool broker authorization boundary | Model output treated as trusted; policy bypass | `tool_broker.py` gates simulation; policy and approval run in broker path | `tests/test_tool_broker.py`, `test_broker_denies_valid_schema_when_policy_denies`, `test_invariant_tool_broker_is_authority_boundary` | Implemented, tested | Broker logic is in-process; not a separate service |
| Human approval gate | High-impact actions without human oversight | `approval_gate.py`; integrated in `tool_broker.py` | `tests/test_approval_gate_integration.py`, `test_send_email_requires_human_approval_via_broker`, `test_export_records_requires_admin_and_approval`, `test_audit_approval_denied` | Implemented, tested | Legacy boolean flag; see approval token row for bound approvals |
| Approval token binding (lab) | Approval replay or wrong-action execution | `approval_tokens.py`; `AgentRequest.approval_token`; broker `require_approval_token` | `tests/test_approval_tokens.py` | Implemented, tested (lab) | In-memory one-time registry; not production IdP or workflow UI |
| Provenance checks | Untrusted context (RAG, user, web, email) authorizing tools | `provenance.py`; `policy_engine.py` | `tests/test_provenance.py`, `test_untrusted_retrieved_cannot_authorize_external_effect`, `test_missing_provenance_blocks_execution` | Implemented, tested | Declarative by default; optional lab HMAC in strict mode |
| Provenance integrity (lab HMAC) | Tampered provenance metadata | `provenance_integrity.py`; strict `broker_tool_request` / pipeline flag | `tests/test_provenance_integrity.py` | Implemented, tested (strict mode) | Lab fake key only; not production PKI; default pipeline does not require signatures |
| Tool-output distrust | Prior tool results treated as instructions or authorization | `ToolOutputSegment`; `prompt.py`; `ProvenanceSource.TOOL_OUTPUT` denied in `provenance.py` | `tests/test_tool_output_injection.py` | Implemented, tested (simulated paths) | Production integrations must classify tool output at ingestion; not all integrations covered |
| Cross-tenant blocking | Cross-tenant data access via tool targets | Tenant match in `policy_engine.py` / broker | `test_cross_tenant_target_denied`, `test_tenant_mismatch_blocks_execution`, `test_audit_cross_tenant_blocked` | Implemented, tested | Demonstration-level isolation; not production multi-tenant hardening |
| Output filtering outside the model | Secret/credential leakage in model text | `output_filter.py` layered filter; runs before broker in `pipeline.py` | `tests/test_output_filter.py`, `test_output_leak_blocked_before_tool_stage`, `test_invariant_output_filter_outside_model`, `test_pipeline_output_filter_audit_has_safe_metadata` | Implemented, tested | Lab heuristics only; not enterprise DLP; destination/schema rules require explicit context |
| JSONL audit logging | Lack of accountability; secret leakage in logs | `audit_logger.py`; redaction in log writer | `tests/test_audit_logger.py`, `tests/test_audit_events.py`, `test_invariant_audit_writes_for_allow_and_block`, `test_audit_no_raw_secrets_in_log` | Implemented, tested | Local JSONL files; not tamper-evident or centralized SIEM |
| Disabled `run_shell` | Remote code execution via shell tools | `policies/default.yaml` (`run_shell: disabled`) | `test_run_shell_disabled_by_policy`, `test_shell_attempt_blocked_on_protected_path`, `test_invariant_denied_tools` | Implemented, tested | Other tools are simulated; policy must stay deny-by-default for new tools |
| Protected path | Control-plane bypass on normal requests | `pipeline.py` full chain; API `path=protected` | `tests/test_pipeline_protected.py`, `test_invariant_protected_path_enforces_control_plane` | Implemented, tested | Caller must select protected path; misconfiguration would weaken posture |
| Vulnerable simulation path | No contrast for unsafe behavior in education | `pipeline.py` vulnerable branch; labels only, no broker | `tests/test_pipeline_vulnerable.py`, `test_invariant_vulnerable_path_simulation_only` | Implemented, tested | Still no real execution; must not be used as production mode |
| Prompt-artifact hygiene scanner | AI transcripts, master prompts, cycle reports in repo | `scripts/validate_repo.py`; `make validate`; `.gitignore` | `tests/test_validate_repo.py` (8 tests), CI repo-hygiene step | Implemented, tested | Heuristic patterns; not a guarantee against all sensitive files |
| Docker validation | Environment drift; non-reproducible validation | `Dockerfile`, `docker-compose.yml`; CI docker job | CI: `docker compose build` + `pytest` (293 tests); local `make validate` | Implemented, tested in CI | Docker optional locally; image does not bind-mount host code |
| Property-based security tests | Edge-case bypass of validators or broker rules | Hypothesis tests in `tests/test_property_*.py`; CI profile in `conftest.py` / `pyproject.toml` | `test_property_schemas.py`, `test_property_broker.py`, `test_property_provenance_integrity.py`, `test_property_approval_tokens.py`, `test_property_output_filter.py`, `test_property_repo_hygiene.py` | Implemented, tested (lab) | Bounded examples only; not exhaustive fuzzing or production certification |
| GitHub Actions CI | Regressions on push/PR | `.github/workflows/ci.yml` | Workflow runs ruff, mypy, pytest, bandit, pip-audit, repo hygiene, policy integrity, Docker | Active on `main` | Node.js 20 deprecation warnings on actions; not formal compliance attestation |
| CodeQL static analysis | Code vulnerabilities in Python sources | `.github/workflows/codeql.yml` | GitHub CodeQL analysis job on push/PR and weekly schedule | Active (P6) | SAST only; triage in GitHub Security; not exhaustive |
| Secret scanning (Gitleaks) | Committed credentials or tokens | `.github/workflows/secrets.yml`; `.gitleaks.toml` | Full-history scan; tests/ allowlist for lab-fake fixtures only | Active (P6) | Heuristic scanner; allowlist scoped to `tests/`; does not scan live environments |
| Container CVE scan (Trivy) | Known vulnerabilities in Docker image | `.github/workflows/trivy.yml` | Build image; fail on CRITICAL/HIGH unfixed | Active (P6) | Base image drift; not runtime pen-test |
| SBOM generation | Dependency transparency for releases | `.github/workflows/sbom.yml` | CycloneDX JSON artifact per run | Active (P6) | Artifact unsigned unless signing added; not a vuln scan |
| Dependabot updates | Dependency and Actions drift | `.github/dependabot.yml` | Weekly pip and GitHub Actions update PRs | Active (P6) | Requires maintainer review; no auto-merge by default |
| Production config validation | Unsafe deployment profile | `config.py`; `AppConfig.validate()` | `tests/test_config.py` | Implemented, tested (P7) | Env-based; operator must set production vars correctly |
| API authentication (production profile) | Unauthorized pipeline invocation | `api.py`; `ACP_REQUIRE_API_AUTH` | `tests/test_api_hardening.py` | Implemented, tested (lab file keys) | File/env keys only; not enterprise IdP |
| Request body size limit | DoS via large HTTP bodies | `MaxBodySizeMiddleware` in `api.py` | `tests/test_api_hardening.py` | Implemented, tested | Content-Length check; proxy limits still required |
| Safe production error responses | Information disclosure via stack traces | `production_error_detail`; exception handlers | `tests/test_config.py`, `tests/test_api_hardening.py` | Implemented, tested | Debug mode available in local profile only |
| Container non-root runtime | Container privilege escalation | `Dockerfile` USER `appuser`; Compose `read_only` | Docker build + pytest in CI | Implemented (P7) | Host mount misconfiguration can weaken posture |
| LLM adapter boundary (simulated default) | Live model output bypassing filter, schema, or broker; unauthorized tool calls from adapter | `llm_adapter.py`; `SimulatedLLMAdapter`; `DisabledExternalLLMAdapter`; pipeline `_generate_model_turn()` | `tests/test_llm_adapter.py` | Implemented, tested (P8) | No live provider client; `ACP_ALLOW_LIVE_LLM_CALLS` rejected at config validation |
| Audit correlation and operational events | Incomplete incident evidence; secret leakage in audit logs | `audit_logger.py`; `observability.py`; `correlation_id` on events; API auth/body-limit/adapter audit | `tests/test_audit_observability.py`, `tests/test_audit_events.py` | Implemented, tested (P9) | JSONL only; not a managed SIEM; heuristic redaction |
| Deployment reference profile | Unsafe deployment; unclear operator vs app boundaries | `docker-compose.production.yml`; `deploy/kubernetes/`; `.env.production.example`; deployment docs | `tests/test_deployment_artifacts.py` | Implemented, tested (P10) | Reference-only manifests; not continuously deployed; no Helm chart in repo |
| Release checksums (unsigned) | Tampered or mistaken release artifacts | `release-artifacts` workflow; `SHA256SUMS` on tag | `tests/test_release_artifacts.py` | Implemented, tested (P12) | Integrity hashes only; not signatures |
| Enterprise integration guidance | False production claims; missing operator boundaries | P11 docs under `docs/enterprise-*.md`, `identity-integration.md`, etc. | `tests/test_enterprise_docs.py` | Documented (P11) | Guidance only; IdP, KMS, SIEM connector, persistent approvals, distributed rate limits not implemented |

## Related documentation

- [docs/defensive-controls.md](docs/defensive-controls.md) — invariants and test names by control
- [docs/threat-model.md](docs/threat-model.md) — threat framing
- [docs/architecture.md](docs/architecture.md) — Mermaid diagrams (control plane, security zones, threat map, validation pipeline)
- [docs/llm-adapter.md](docs/llm-adapter.md) — LLM adapter trust boundary and integration requirements
- [docs/audit-event-taxonomy.md](docs/audit-event-taxonomy.md) — audit event types and review guidance
- [docs/siem-export.md](docs/siem-export.md) — SIEM ingestion patterns (documentation only)
- [docs/audit-review-playbook.md](docs/audit-review-playbook.md) — operator review checklists
- [docs/operator-runbook.md](docs/operator-runbook.md) — day-two operations
- [docs/deployment-boundaries.md](docs/deployment-boundaries.md) — enforced vs operator controls
- [docs/deployment-checklist.md](docs/deployment-checklist.md) — pre/post deploy checks
- [docs/helm-guidance.md](docs/helm-guidance.md) — Helm values patterns (no bundled chart)
- [docs/enterprise-integration-plan.md](docs/enterprise-integration-plan.md) — enterprise integration boundaries (guidance only)
- [docs/enterprise-readiness-checklist.md](docs/enterprise-readiness-checklist.md) — operator readiness gates
- [README.md](README.md#architecture) — summary architecture diagrams
- [docs/defensive-controls.md](docs/defensive-controls.md) — security invariants
- [SECURITY.md](SECURITY.md) — reporting vulnerabilities

## Validation baseline

Re-run `make validate` (includes policy integrity) before relying on this matrix for a fork or deployment decision. Policy hash drift is caught by `python scripts/validate_policy.py` and CI.
