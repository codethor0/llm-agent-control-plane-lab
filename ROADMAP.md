# Roadmap

This project is a **defensive reference lab**, not a production agent platform. Roadmap items extend the control plane model with tested security behavior. Items are not committed until they have tests and documentation.

## Near term (post v0.1.0)

| Item | Goal |
|------|------|
| GitHub remote and CI on `main` | Public repository with passing Actions workflow |
| Architecture diagram assets | `docs/assets/` PNG/SVG for README and talks |
| GitHub release `v0.1.0` | Tagged release with validated notes |
| Issue and PR templates | Contributor workflow (added in repo) |

## Security and policy

| Item | Description |
|------|-------------|
| Signed provenance | Cryptographic attestation for tool-call provenance instead of declarative metadata only |
| OPA/Rego policy backend | Optional policy engine behind the same broker interface |
| Security control maturity matrix | Document control strength and test coverage per threat |
| Additional output-filter rules | Safe detectors for new leak patterns with positive/negative tests |

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
| GitHub issue templates | Bug, security gap, docs, feature request (see `.github/ISSUE_TEMPLATE/`) |
| Discussion guidelines | When to use issues vs discussions for lab questions |

## Non-goals

- Real shell execution from model output
- Live exploitation or third-party target testing
- Jailbreak libraries or offensive tooling
- Claims of universal LLM safety or production certification

See [docs/provenance.md](docs/provenance.md) for current provenance limitations.
