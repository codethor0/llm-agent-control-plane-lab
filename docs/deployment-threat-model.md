# Deployment Threat Model

This threat model covers **deployment and operations** of the llm-agent-control-plane reference API and container. It complements [docs/threat-model.md](threat-model.md) (agent and control-plane logic).

**Scope:** Network-exposed demo API, configuration, audit logs, container runtime, and supply chain.  
**Out of scope:** Live LLM provider abuse, real shell execution, third-party target testing.

## Assets

| Asset | Description |
|-------|-------------|
| Policy YAML | Tool rules, deny-by-default configuration |
| API keys | Gate access to `/run` in production profile |
| Provenance HMAC key | Signs provenance metadata in strict mode |
| Approval tokens | One-time authorization for high-impact tools (lab registry) |
| Audit JSONL | Allow/deny decisions with redacted metadata |
| Container image | Python runtime and dependencies |
| SBOM artifact | Dependency transparency from CI |

## Trust boundaries

```
[Internet / users]
        |
        v
[TLS terminator / WAF / rate limiter]  <-- operator-controlled
        |
        v
[FastAPI demo API]  <-- ACP_* config, auth on /run
        |
        v
[Control plane pipeline]  <-- broker, policy, filter (in-process)
        |
        v
[LLM adapter - simulated by default]  <-- candidate output only; no tool authority
        |
        v
[Simulated tools]  <-- no real external execution
```

Untrusted: all HTTP request bodies, headers (except validated API keys), and **all** LLM adapter output (treated as untrusted candidate text before output filter and broker).

## Attacker goals

- Invoke tools without broker authorization
- Bypass output filter or approval gates
- Steal API keys or audit data
- Tamper with policy or configuration at rest
- Abuse unauthenticated or oversized requests
- Escape container to host (limited by non-root and read-only rootfs)

## Deployment assumptions

- Operators deploy behind TLS and network policies
- Production profile validation runs at application startup
- API keys are stored in a secret manager, not in git
- Simulated tools remain the only execution path
- Organizational review occurs before production exposure

## Threats and mitigations

### API abuse

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Unauthenticated `/run` calls | `ACP_REQUIRE_API_AUTH` in production | Misconfiguration if env vars wrong |
| Brute-force API keys | Edge rate limiting (operator) | Not enforced in app |
| Large body DoS | `MaxBodySizeMiddleware` + proxy limits | Streaming bodies not fully buffered-checked |
| Credential stuffing | Rotate keys; monitor 401 rates | Operator responsibility |

### Configuration tampering

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Weak production config | `AppConfig.validate()` fail-closed | Process must call `validate()` |
| Wildcard CORS | Rejected in production mode | Local mode still allows lab origins |
| Debug errors leak internals | `ACP_ENABLE_DEBUG_ERRORS=false` in production | Mis-set env in deployment |
| Enabling live tools via config | `allow_live_external_tools` must stay false | Code change could alter defaults |

### Audit log threats

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Tampering with JSONL files | Forward to append-only SIEM | Local files are mutable |
| Secret leakage in logs | Redaction tests in `test_audit_logger.py` | New fields need redaction review |
| Retention failure | `ACP_AUDIT_RETENTION_DAYS` + operator archival | Not automated in app |

### Approval replay

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Token reuse | One-time registry in lab | In-memory only; not production store |
| Wrong-action approval | Action hash binding in `approval_tokens.py` | Requires `ACP_REQUIRE_APPROVAL_TOKEN` |

### Provenance tampering

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Forged provenance | HMAC in strict mode | Lab key only; not PKI |
| Missing provenance | Broker denies by default | Integrator must classify sources |

### Container escape

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Root compromise | Non-root `appuser` | Kernel CVEs still apply |
| Writable rootfs abuse | `read_only` + tmpfs in Compose | Host mount misconfiguration |
| Supply-chain compromise | Trivy, SBOM, Dependabot (P6) | Point-in-time scans |

### Supply chain

| Threat | Mitigation | Residual risk |
|--------|------------|---------------|
| Vulnerable dependencies | pip-audit, Dependabot | Review lag |
| Secrets in git | Gitleaks CI | Cannot detect all secret types |
| Malicious GitHub Actions | Pinned action versions | Third-party action trust |

## Non-goals

- Protecting against compromised operator with root on the host
- Preventing all prompt-injection outcomes inside a connected live LLM (simulated core only)
- Replacing enterprise IdP, WAF, or SOC operations
- Formal verification of the control plane

## Verification

| Control | Tests / checks |
|---------|----------------|
| Config validation | `tests/test_config.py` |
| API auth and body limits | `tests/test_api_hardening.py` |
| Broker and policy | Existing security test suite |
| Container non-root | `Dockerfile` USER directive |
| Supply chain | GitHub Actions workflows |

Re-run `make validate` before each release.
