# LinkedIn launch post

Defensive reference lab: external control plane for tool-connected LLM agents

I published an open-source lab that demonstrates how to keep authorization, policy, provenance checks, human approval, output filtering, and audit logging outside the model.

Core idea: the model can ask. The broker decides.

What it includes:
- Deny-by-default policy and tool broker as the authority boundary
- Schema validation that does not imply authorization
- Provenance rules and human approval for high-impact tools
- Output filtering and redacted JSONL audit events
- 83 automated tests mapped to defensive controls
- Simulated tools only (no real shell, email, or network execution)

What it is not:
- A production agent platform
- A jailbreak or exploit toolkit
- A guarantee against all prompt injection

Repository: https://github.com/codethor0/llm-agent-control-plane-lab
Release v0.1.0: https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.0

Use in authorized local lab environments only. Feedback and control-gap issues welcome on GitHub.
