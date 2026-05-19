# Rate Limiting and Edge Controls

**Status:** Guidance only. **Distributed rate limiting is not implemented** in the application.

## Why rate limiting belongs at the edge

| Reason | Detail |
|--------|--------|
| Abuse volume | `/run` can be expensive; stop traffic before Python work |
| Identity context | Gateway knows client IP, API key, or JWT subject |
| Horizontal scale | Per-replica in-app limits are inconsistent without shared state |
| Defense in depth | Complements `ACP_MAX_REQUEST_BODY_BYTES` in app |

The app enforces **request body size** via middleware (`tests/test_api_hardening.py`). It does **not** enforce requests-per-second limits.

## Request size limits already implemented

| Control | Config | Tested |
|---------|--------|--------|
| Max body bytes | `ACP_MAX_REQUEST_BODY_BYTES` | Yes |
| Audit on block | `request_body_limit_blocked` | Yes |

Configure matching limits on nginx, Envoy, API Gateway, or cloud LB.

## API gateway placement

```text
Internet --> WAF --> API gateway (auth + rate limit) --> llm-agent-control-plane
```

Gateway responsibilities:

- Authentication (see [identity-integration.md](identity-integration.md))
- Rate limits and quota per tenant
- TLS termination
- Optional mTLS for internal callers

## Per-user and per-tenant limits

| Dimension | Example policy |
|-----------|----------------|
| Per API key | 100 req/min (dev integrations) |
| Per tenant | 1000 req/min |
| Per user (JWT sub) | 60 req/min |
| Burst | Allow short burst with token bucket |

Map limits to organizational tiers. Document in runbooks.

## Abuse detection

Combine rate limits with SIEM rules ([siem-onboarding-plan.md](siem-onboarding-plan.md)):

- Spike in `api_auth_failure`
- High `schema_validation_failed` rate (malformed automation)
- Repeated `provenance_denied` (injection probes)

## Backpressure

When overloaded, gateway should return `429` or `503` with `Retry-After`. The app does not coordinate cluster-wide backpressure.

## WAF considerations

WAF rules may block obvious injection payloads at HTTP layer. **WAF is not a substitute** for broker and provenance controls inside the app.

## mTLS optional patterns

Service mesh mTLS between gateway and app pods adds service identity. Configure at platform level; not in this repository.

## Tests needed before in-app rate limiting

If future in-app limiting is proposed:

- Per-tenant limit returns safe denial with audit event
- Limit does not bypass broker for allowed requests under threshold
- Property: limiter cannot be skipped via alternate API paths
- Load tests in CI are **not** required for P11; document operational testing separately

Until then, document `ACP_ENABLE_RATE_LIMIT_GUIDANCE` as operator responsibility at edge.

## Related docs

- [enterprise-integration-plan.md](enterprise-integration-plan.md)
- [production-hardening.md](production-hardening.md)
- [deployment-boundaries.md](deployment-boundaries.md)
