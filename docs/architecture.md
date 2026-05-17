# Architecture

## Overview

This lab implements an **external control plane** around a simulated LLM agent. The model may propose tool calls; only the broker and policy engine may authorize execution. All tools run through a local simulator.

## Flow

```text
Untrusted input (user + retrieved)
        |
        v
  Prompt assembly
        |
        v
  Simulated agent core  (untrusted output)
        |
        v
  Output filter         (block leaks)
        |
        v
  Schema validation     (structure only)
        |
        v
  Tool broker           (authority boundary)
        |-> policy engine (deny by default, roles, tenant, provenance)
        |-> approval gate (human approval for high-impact tools)
        |
        v
  Simulated tool execution
        |
        v
  Audit logger (JSONL, redacted)
```

## Paths

| Path | Behavior |
|------|----------|
| **Protected** | Full pipeline: filter, schema, broker, policy, approval, simulation, audit |
| **Vulnerable** | Skips broker/policy; records labeled unsafe simulation only |

## Modules

| Module | Role |
|--------|------|
| `prompt.py` | Assembles prompts; does not grant authority |
| `agent_core.py` | Deterministic simulated model output |
| `schemas.py` | Pydantic argument shapes |
| `tool_broker.py` | Authority boundary |
| `policy_engine.py` | YAML policy evaluation |
| `approval_gate.py` | Human approval gate (wired in broker) |
| `provenance.py` | Declarative provenance rules |
| `output_filter.py` | Blocks secrets, keys, JWT-like tokens, blobs |
| `audit_logger.py` | JSONL audit with redaction |
| `simulator.py` | Safe simulated tools |
| `pipeline.py` | Orchestration |
| `api.py` | FastAPI local demo |

## Trust boundaries

- **Trusted:** static policy file, broker code, output filter, audit redaction logic
- **Untrusted:** user messages, retrieved chunks, all model output including tool calls

## Provenance

See [provenance.md](provenance.md). Provenance is declarative metadata today, not signed attestation.

## Non-goals

- Real LLM API integration
- Real shell, email, or network execution
- Multi-tenant production isolation beyond demonstration checks
