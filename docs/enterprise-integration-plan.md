# Enterprise Integration Plan (P11)

**Status:** Guidance and planning only. **Not** a production integration implementation.

This document explains how organizations should connect **llm-agent-control-plane** to enterprise identity, key management, approval workflows, SIEM, rate limiting, deployment ownership, and platform controls. It does **not** make this repository a drop-in production platform.

## Purpose

Security and platform teams need a single map of:

1. What the reference app enforces today (tested in this repo).
2. What operators must provide at the edge, in infrastructure, and in operations.
3. How future implementations should be validated before claims are added to [SECURITY-CONTROLS.md](../SECURITY-CONTROLS.md).

## What the app enforces today

| Area | In-repo control | Tests |
|------|-----------------|-------|
| Deny-by-default policy | `policy_engine.py`, `policies/default.yaml` | `tests/test_policy_engine.py`, integrity script |
| Tool broker boundary | `tool_broker.py` | `tests/test_tool_broker.py` |
| Schema validation (structure only) | `schema_validation.py` | `tests/test_schema_validation.py` |
| Provenance rules | `provenance.py` | `tests/test_provenance.py` |
| Lab approval tokens (in-memory) | `approval_tokens.py` | `tests/test_approval_tokens.py` |
| Output filter | `output_filter.py` | `tests/test_output_filter.py` |
| Audit JSONL + redaction | `audit_logger.py` | `tests/test_audit_logger.py` |
| Production config profile | `config.py` | `tests/test_config.py` |
| API auth (file keys) | `api.py` | `tests/test_api_hardening.py` |
| Request body size limit | `MaxBodySizeMiddleware` | `tests/test_api_hardening.py` |
| Simulated tools only | `simulator.py`, policy | pipeline and invariant tests |

See [deployment-boundaries.md](deployment-boundaries.md) for the enforced vs operator matrix.

## What operators must provide

| Capability | Owner | Reference doc |
|------------|-------|---------------|
| Enterprise identity (OIDC/SAML) | Platform / IAM | [identity-integration.md](identity-integration.md) |
| KMS or secret manager | Security / platform | [kms-secret-management.md](kms-secret-management.md) |
| Persistent approvals + workflow UI | App owner / GRC | [approval-workflow.md](approval-workflow.md) |
| SIEM ingestion and alerting | SOC | [siem-onboarding-plan.md](siem-onboarding-plan.md) |
| Rate limiting and WAF | Edge / API platform | [rate-limiting-edge-controls.md](rate-limiting-edge-controls.md) |
| TLS, ingress, network policy | Platform | [production-hardening.md](production-hardening.md) |
| Audit retention and legal hold | Compliance / ops | [operator-runbook.md](operator-runbook.md) |
| Branch protection and release trust | Engineering leadership | [branch-protection.md](branch-protection.md), [release-provenance.md](release-provenance.md) |

## Reference enterprise architecture

```text
                    +------------------+
                    |  IdP (OIDC/SAML)|
                    +--------+---------+
                             |
                    +--------v---------+
                    | API gateway /    |
                    | reverse proxy    |
                    | (authn, rate     |
                    |  limit, TLS)     |
                    +--------+---------+
                             |
                    +--------v---------+
                    | llm-agent-       |
                    | control-plane    |
                    | (broker, policy, |
                    |  audit JSONL)    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v----+  +------v------+ +-----v------+
     | KMS /       |  | Approval    | | Log        |
     | secrets     |  | workflow    | | forwarder  |
     +-------------+  +-------------+ +-----+------+
                                              |
                                       +------v------+
                                       | SIEM / SOC  |
                                       +-------------+
```

The gateway terminates enterprise identity and applies abuse controls **before** requests reach the app. The app continues to enforce broker, policy, provenance, and output filter rules on every `/run` request.

## Integration topics (guidance index)

| Topic | Document |
|-------|----------|
| Identity provider | [identity-integration.md](identity-integration.md) |
| KMS and secrets | [kms-secret-management.md](kms-secret-management.md) |
| Approvals | [approval-workflow.md](approval-workflow.md) |
| SIEM | [siem-onboarding-plan.md](siem-onboarding-plan.md) |
| Rate limits and edge | [rate-limiting-edge-controls.md](rate-limiting-edge-controls.md) |
| Readiness checklist | [enterprise-readiness-checklist.md](enterprise-readiness-checklist.md) |

## Production readiness gates

Before calling a deployment "enterprise production," operators should complete [enterprise-readiness-checklist.md](enterprise-readiness-checklist.md) and [deployment-checklist.md](deployment-checklist.md). Green CI in this repository is necessary but not sufficient.

| Gate | Requirement |
|------|-------------|
| Identity | IdP-integrated gateway; no long-lived shared API keys as sole control |
| Secrets | Keys from KMS/secret manager; rotation documented |
| Approvals | Persistent store + auditable approver identity |
| SIEM | Forwarding, detections, on-call routing |
| Abuse | Per-tenant rate limits at edge |
| Release | Tag discipline, SHA256SUMS verification ([artifact-verification.md](artifact-verification.md)) |
| Legal | Data classification and retention sign-off |

## Non-goals (P11)

- Implementing OIDC/SAML inside the app
- Bundling a managed SIEM connector or agent
- Shipping a persistent approval database
- Distributed in-app rate limiting
- Claiming regulated production certification
- Replacing organizational SOC, IAM, or compliance programs

## Related documentation

- [security-gap-assessment.md](security-gap-assessment.md)
- [v0.2.0-hardening-plan.md](v0.2.0-hardening-plan.md)
- [production-hardening.md](production-hardening.md)
