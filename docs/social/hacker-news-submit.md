# Hacker News submission

Title:

Show HN: Defensive LLM agent control plane lab (simulated tools, 83 tests, deny-by-default)

URL:

https://github.com/codethor0/llm-agent-control-plane-lab

Optional comment (post as reply if needed):

I built a small Python reference lab for securing tool-connected LLM agents with an external control plane.

The model proposes structured tool calls; a broker enforces policy, provenance, roles, tenant isolation, human approval, and output filtering before any simulated execution. Schema validation is structural only.

Includes FastAPI demo, CLI scenarios, Docker validation, and 83 tests. No real shell or external tool execution. Vulnerable path is simulation-only for contrast.

Release v0.1.0: https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.0

Looking for feedback from defenders and builders on control-plane patterns, not feature requests for production LLM wiring.
