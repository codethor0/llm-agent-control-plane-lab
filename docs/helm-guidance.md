# Helm Deployment Guidance

This repository does **not** ship a maintained Helm chart. This document describes recommended values and patterns if you create an organizational chart wrapping the control-plane image.

**Not production-certified.** Review with your platform and security teams.

## Recommended chart structure

| Resource | Purpose |
|----------|---------|
| Deployment | API workload with `securityContext` |
| Service | ClusterIP on port 8080 |
| ConfigMap | Non-secret `ACP_*` variables |
| Secret | API keys file (`api_keys.txt` key) |
| Ingress | TLS termination and host rules |
| NetworkPolicy | Restrict ingress sources |
| PersistentVolumeClaim or emptyDir | Audit log volume (operator choice) |

## Example values.yaml (reference)

```yaml
image:
  repository: your-registry.example.invalid/llm-agent-control-plane
  tag: v0.2.6
  pullPolicy: IfNotPresent

replicaCount: 1

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: control-plane.example.invalid
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: control-plane-tls
      hosts:
        - control-plane.example.invalid

env:
  ACP_ENVIRONMENT: production
  ACP_REQUIRE_API_AUTH: "true"
  ACP_ENABLE_DEBUG_ERRORS: "false"
  ACP_ALLOWED_ORIGINS: "https://app.example.invalid"
  ACP_ALLOW_LIVE_EXTERNAL_TOOLS: "false"
  ACP_ALLOW_SHELL_TOOLS: "false"
  ACP_LLM_ADAPTER_MODE: simulated
  ACP_ALLOW_LIVE_LLM_CALLS: "false"
  ACP_AUDIT_LOG_DIR: /tmp/audit
  ACP_AUDIT_RETENTION_DAYS: 90

existingSecret: llm-control-plane-api-keys
existingSecretKey: api_keys.txt
existingSecretMountPath: /run/secrets/api_keys.txt

securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL

podSecurityContext:
  seccompProfile:
    type: RuntimeDefault

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 15

readinessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5

networkPolicy:
  enabled: true

auditVolume:
  enabled: true
  sizeLimit: 128Mi
```

## Helm lint

If you add a chart under `deploy/helm/` in a fork, run:

```bash
helm lint deploy/helm/control-plane
```

Helm is **not** required for this repository's CI. Absence of a bundled chart is intentional for this cycle.

## Operator responsibilities

| Item | Owner |
|------|-------|
| Image build and pinning | Operator |
| TLS certificates | Operator |
| API key rotation | Operator |
| Rate limiting | Ingress/gateway operator |
| SIEM forwarding | Operator |
| Production config validation | Operator at deploy time |

## Related documents

- [deploy/kubernetes/README.md](../deploy/kubernetes/README.md)
- [deployment-boundaries.md](deployment-boundaries.md)
- [deployment-checklist.md](deployment-checklist.md)
