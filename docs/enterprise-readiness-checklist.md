# Enterprise Readiness Checklist

Use before exposing **llm-agent-control-plane** to enterprise users or regulated data. This checklist is **operator-owned**. Passing items here does not imply the open-source repo is a certified production product.

See [enterprise-integration-plan.md](enterprise-integration-plan.md) for architecture context.

## Identity

- [ ] Corporate IdP integrated at **API gateway** (OIDC/SAML) — **not provided by this repo**
- [ ] `user_id`, `tenant_id`, `role` mapped from trusted claims, not client-spoofable headers
- [ ] Static API keys not the sole production control
- [ ] Auth failure monitoring in SIEM

## Secrets and keys

- [ ] No secrets in git; Gitleaks green on deploy branch
- [ ] API keys and HMAC keys from KMS/secret manager
- [ ] Key rotation runbook documented
- [ ] Container images do not embed production keys

## Approvals

- [ ] High-impact tools require human approval in organizational policy
- [ ] Persistent approval store planned or deployed — **not in repo today**
- [ ] Approver identity recorded for audit
- [ ] Revocation process defined

## SIEM

- [ ] JSONL forwarded to enterprise SIEM — **connector not bundled**
- [ ] Parsers map `event_type`, `correlation_id`, tenant fields
- [ ] Detections for provenance, output filter, auth failures
- [ ] Retention meets compliance requirements

## Rate limits

- [ ] Per-tenant and per-user limits at gateway — **not in-app**
- [ ] Request body limits aligned with `ACP_MAX_REQUEST_BODY_BYTES`
- [ ] Abuse playbooks linked to SOC

## Network

- [ ] TLS terminated at ingress with current ciphers
- [ ] Private networking; `/run` not public without gateway
- [ ] NetworkPolicy or equivalent reviewed (reference K8s manifests are starting points only)
- [ ] Egress restricted per organizational policy

## Deployment

- [ ] [deployment-checklist.md](deployment-checklist.md) complete
- [ ] Production profile: auth, CORS, debug off, simulated tools only
- [ ] Policy integrity hash verified at deploy
- [ ] Non-root container, read-only rootfs where used

## Release verification

- [ ] [release-security-checklist.md](release-security-checklist.md) complete for deployed version
- [ ] SHA256SUMS verified for tagged release ([artifact-verification.md](artifact-verification.md))
- [ ] Understand checksums are **unsigned**

## Branch protection

- [ ] `main` protected per [branch-protection.md](branch-protection.md)
- [ ] Required reviews before merge to deploy branch

## Incident response

- [ ] [operator-runbook.md](operator-runbook.md) and [audit-review-playbook.md](audit-review-playbook.md) adopted
- [ ] On-call rotation and escalation paths defined
- [ ] Tabletop exercise for broker bypass or secret leak scenarios

## Ownership model

| Area | Owner |
|------|-------|
| Application policy YAML | App security / engineering |
| Broker behavior upgrades | Upstream repo + fork maintainers |
| IdP, gateway, WAF | Platform / IAM |
| SIEM | SOC |
| KMS | Security engineering |
| Approvals workflow | GRC + app owner |

## Legal and compliance review

- [ ] Data classification for prompts and audit logs
- [ ] Retention and deletion aligned with regulation
- [ ] Third-party LLM usage reviewed (adapter remains simulated in repo)
- [ ] No claim of universal compliance from this checklist alone

## Honest boundaries

This project remains a **production-oriented defensive reference implementation**. P11 adds guidance only; it does not implement enterprise IdP, KMS, persistent approvals, managed SIEM, or distributed rate limiting.
