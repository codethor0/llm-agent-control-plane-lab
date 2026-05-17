# Roadmap

This project is a **defensive reference lab**, not a production agent platform. Roadmap items extend the control plane model with tested security behavior. Items are not committed until they have tests and documentation.

## Completed (v0.1.x)

| Item | Status |
|------|--------|
| Public GitHub repo and CI | Done |
| Mermaid architecture diagrams and README badges | Done (main) |
| SECURITY-CONTROLS.md matrix | Done |
| Architecture SVG/PNG assets | Done |
| Releases v0.1.0, v0.1.1, v0.1.2 | Done |
| Fresh-clone and hygiene scanner fixes | Done (84 tests) |
| Issue and PR templates | Done |

## v0.2.0 — Security hardening (planned)

Theme: **depth over aesthetics**. See [docs/v0.2.0-hardening-plan.md](docs/v0.2.0-hardening-plan.md) and [docs/security-gap-assessment.md](docs/security-gap-assessment.md).

| Priority | Work package | Status |
|----------|--------------|--------|
| P0 | Policy integrity (schema, hash, CI verification) | Done |
| P1 | Signed or hashed provenance (lab HMAC mode) | Done |
| P2 | Tool-output injection tests | Done |
| P3 | Approval token model (ID, expiry, action hash) | Done |
| P4 | Output filter layers (entropy, tenant-aware) | Planned |
| P5 | Hypothesis fuzz tests | Planned |
| P6 | Supply-chain (Dependabot, CodeQL, gitleaks, Trivy, SBOM) | Planned |
| P7 | Production hardening documentation | Planned |
| P8 | LLM adapter interface (no live API by default) | Planned |

**v0.2.0 release bar (minimum):** P0 through P3 complete with tests; `make validate` green.

## Security and policy (ongoing)

| Item | Description |
|------|-------------|
| OPA/Rego policy backend | Optional policy engine behind the same broker interface |
| Security control maturity matrix | Extend SECURITY-CONTROLS with maturity levels per gap |
| Additional output-filter rules | Safe detectors with positive/negative tests |

## Observability and CI

| Item | Description |
|------|-------------|
| OpenTelemetry tracing | Spans aligned with `request_id` across pipeline stages |
| SARIF output | Export bandit/ruff/security findings for CI ingestion |
| Approval workflow examples | Documented patterns for human-in-the-loop gates |

## Scenarios and agents

| Item | Description |
|------|-------------|
| Browser-agent simulation | Safe simulated browser tool path with broker enforcement |
| Multi-tenant test scenarios | Expanded cross-tenant and isolation test matrix |
| More policy fixtures | Additional YAML policies for education and regression |

## Community

| Item | Description |
|------|-------------|
| Discussion guidelines | When to use issues vs discussions for lab questions |

## Non-goals

- Real shell execution from model output
- Live exploitation or third-party target testing
- Jailbreak libraries or offensive tooling
- Claims of universal LLM safety or production certification

See [docs/provenance.md](docs/provenance.md) for current provenance limitations.
