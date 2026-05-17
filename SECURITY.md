# Security Policy

## Scope

This policy applies to the **llm-agent-control-plane** repository only: a production-oriented defensive reference implementation for educational and authorized local testing. It is not a product security program for downstream deployments.

## Supported versions

| Version | Supported |
|---------|-----------|
| `main`  | Yes       |

## Reporting a vulnerability

If you believe you have found a security issue in this repository:

1. **Do not** open a public GitHub issue for exploitable findings.
2. Email the maintainers via the contact method listed in the repository profile, or open a **private** security advisory on GitHub if enabled for this repo.
3. Include: description, impact, reproduction steps safe for local lab use only, and suggested fix if known.

We will acknowledge receipt within a reasonable timeframe and coordinate disclosure.

## Out of scope

- Third-party systems, live targets, or production environments you do not own.
- Requests to add real exploitation, jailbreak libraries, malware samples, or offensive tooling.
- Findings that require disabling documented security controls to demonstrate (report the bypass of the control instead).

## Safe testing

Test only against your local clone using the documented `make demo` and pytest flows. Do not use this project to attack external services.

## Security claims

Claims about controls are backed by tests under `tests/`. If a control lacks tests, treat it as not implemented.
