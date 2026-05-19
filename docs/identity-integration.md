# Identity Integration Guidance

**Status:** Planning guidance only. **OIDC and SAML are not implemented** in this repository.

## Recommended IdP patterns

| Pattern | Description | Fits this project |
|---------|-------------|-------------------|
| Gateway front door | API gateway or reverse proxy validates JWT/session from corporate IdP before proxying to `/run` | **Recommended** |
| Service mesh identity | mTLS + SPIFFE/SPIRE or mesh identity for service-to-service | Optional for internal callers |
| Static API keys (file) | `ACP_REQUIRE_API_AUTH` + key file | **Lab / dev only**; not enterprise production |

Enterprise production should treat the gateway as the **authentication boundary**. The app receives already-authenticated context via trusted headers or mTLS client identity injected by the platform (design your integration carefully; never trust client-supplied `user_id` without gateway validation).

## OIDC or SAML front-door gateway pattern

```text
Client --> IdP (login) --> Gateway (JWT validate) --> /run (ACP API)
```

1. User or service authenticates to IdP (OIDC authorization code, client credentials, or SAML SSO).
2. Gateway validates tokens (issuer, audience, expiry, signature).
3. Gateway maps claims to `user_id`, `tenant_id`, and `role` for the JSON body or internal session.
4. Gateway forwards only to allowed origins (CORS remains app-enforced; gateway may also enforce).

**Not in repo:** gateway configuration, IdP metadata, client secrets, or token validation code.

## Mapping enterprise identity to request fields

The `/run` API accepts `user_id`, `tenant_id`, `role`, and related fields. In enterprise deployments:

| Field | Source | Notes |
|-------|--------|-------|
| `user_id` | IdP `sub` or workforce ID | Must be stable for audit correlation |
| `tenant_id` | IdP org claim or platform partition | Required for cross-tenant tests in lab |
| `role` | IdP groups mapped to app roles | Map `admin` only where policy requires |
| `session_id` | Gateway session or trace ID | Supports incident timelines |

The broker and policy engine use these fields; they do **not** validate IdP tokens themselves.

## Why static API keys are not enough for enterprise production

| Limitation | Risk |
|------------|------|
| Shared keys | No per-user attribution; blast radius on leak |
| File-based keys | Rotation requires redeploy; easy to commit by mistake |
| No step-up auth | High-impact tools need human approval tied to real identity |

File-based keys in this repo exist for **lab and integration testing** only (`tests/test_api_hardening.py`).

## Required audit fields

Ensure forwarded requests produce audit events with:

- `user_id`, `tenant_id`, `role` (from trusted mapping)
- `correlation_id` (client or gateway generated)
- `request_id`, `session_id`
- Auth failure events at gateway **and** app (`api_auth_failure` when app auth enabled)

See [audit-event-taxonomy.md](audit-event-taxonomy.md).

## Failure modes

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Gateway bypass | Direct `/run` without auth | Network policy; require auth on all paths except `/health` |
| Spoofed identity headers | Wrong tenant access | Strip client headers; gateway injects identity |
| Stale group membership | Over-privileged role | Short JWT TTL; periodic group sync |
| Missing correlation ID | Broken SIEM timelines | Enforce `X-Correlation-ID` at gateway |

## Tests required before future implementation

Any future in-app OIDC middleware must add:

- Positive: valid token maps to allowed `/run`
- Negative: expired, wrong audience, missing scope denied
- Negative: tampered JWT denied
- Audit: `api_auth_failure` with safe metadata (no token material in logs)
- Property: spoofed `user_id` in body cannot override gateway identity if both present

Until those tests exist, **do not claim IdP integration in SECURITY-CONTROLS.md**.

## Related docs

- [enterprise-integration-plan.md](enterprise-integration-plan.md)
- [production-hardening.md](production-hardening.md)
- [deployment-boundaries.md](deployment-boundaries.md)
