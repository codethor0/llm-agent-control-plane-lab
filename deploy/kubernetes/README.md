# Kubernetes Reference Manifests

**Reference only.** These manifests illustrate a safer default deployment shape for the control-plane API. They are **not** certified for production, not continuously deployed by this repository, and require your platform team's review.

## What this provides

- Non-root `securityContext` with dropped capabilities
- Read-only root filesystem with writable audit volume
- Liveness and readiness probes on `/health`
- ConfigMap for non-secret environment variables
- `secret.example.yaml` for API key shape (copy to your secret manager workflow)
- Optional NetworkPolicy restricting ingress

## What operators must provide

- Container image build and registry (pin by digest or immutable tag)
- TLS termination (Ingress or service mesh)
- Real API keys via Kubernetes Secrets or external secret operator
- Rate limiting at ingress or gateway
- SIEM forwarding for audit JSONL on the mounted volume
- Resource sizing for your traffic profile
- Pod Security Standards / admission policy alignment

## Apply (local lab only)

```bash
# Build image locally first
docker compose -f docker-compose.production.yml build

# Load into kind/minikube if needed, then:
kubectl apply -f deploy/kubernetes/configmap.yaml
# Create Secret from secret.example.yaml in your cluster (do not commit real secrets)
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/networkpolicy.yaml
```

Replace image reference in `deployment.yaml` with your registry and pinned tag.

## Related documents

- [docs/deployment-boundaries.md](../../docs/deployment-boundaries.md)
- [docs/deployment-checklist.md](../../docs/deployment-checklist.md)
- [docs/helm-guidance.md](../../docs/helm-guidance.md)
