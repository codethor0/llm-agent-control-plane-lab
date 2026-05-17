# llm-agent-control-plane-lab

[![CI](https://github.com/OWNER/llm-agent-control-plane-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/llm-agent-control-plane-lab/actions/workflows/ci.yml)

Defensive open source reference lab for securing tool-connected LLM agents with an **external control plane**.

**Core idea:** The model can ask. The broker decides.

Replace `OWNER` in the CI badge URL after you create the GitHub repository.

## One-command quick start

Requires **Python 3.12** (see [Python version](#python-version)).

```bash
make setup && make demo
```

Full validation (including Docker when the daemon is running):

```bash
make setup && make validate
```

## Python version

| Environment | Python |
|-------------|--------|
| Project target | **3.12.x** (`requires-python = >=3.12,<3.13`) |
| Docker / GitHub Actions | 3.12 |
| Local host on 3.14+ | **Mismatch** — use `pyenv install 3.12`, `asdf`, or Docker |

Verify your venv:

```bash
.venv/bin/python scripts/check_python_version.py
```

## Docker quick start

```bash
docker compose build
docker compose run --rm app python -m pytest
make demo   # host Python 3.12 venv, or run demo inside the image
```

### Docker troubleshooting

| Symptom | Action |
|---------|--------|
| `Cannot connect to the Docker daemon` | Start Docker Desktop or the system Docker service, then retry `docker compose build`. |
| Build fails on `pip install` | Ensure network access; rebuild with `docker compose build --no-cache`. |
| Tests differ from host | Docker runs the image copy of the code (no bind mounts). Rebuild after changes. |

Docker validation is **not** claimed unless `docker compose build` and `docker compose run --rm app python -m pytest` succeed on your machine.

## What this repo does

- Demonstrates a deterministic **external control plane** around a simulated LLM agent
- Enforces **deny-by-default** policy, **tool broker** authorization, **provenance** rules, **human approval**, and **output filtering**
- Writes structured, **redacted JSONL** audit events
- Provides a local **FastAPI** API and **CLI demo**
- Maps [security invariants](docs/defensive-controls.md) to automated tests

## What this repo does not do

- Call production LLM APIs by default
- Execute real shell commands, send real email, or scan networks
- Store or exfiltrate real credentials
- Provide exploit chains, jailbreak libraries, or offensive tooling
- Test or attack third-party systems

## Architecture flow

```text
Untrusted input -> prompt -> simulated model (untrusted)
  -> output filter -> schema validation (structure only)
  -> tool broker -> policy engine + provenance + approval gate
  -> simulated tools -> audit log (JSONL, redacted)
```

Details: [docs/architecture.md](docs/architecture.md), [docs/threat-model.md](docs/threat-model.md), [docs/provenance.md](docs/provenance.md).

## Demo scenarios

| Scenario | Protected path |
|----------|----------------|
| `safe_read` | Allowed (simulated read) |
| `internal_reviewed_read` | Allowed (internal reviewed provenance) |
| `shell_attempt` | Blocked (`run_shell` disabled) |
| `injection_send_email` | Blocked (retrieved provenance) |
| `send_email_approved` + `human_approval=true` | Allowed |
| `output_secret_leak` | Blocked (output filter) |
| `export_no_approval` | Blocked (approval gate) |
| `export_approved` + `role=admin` + `human_approval=true` | Allowed |
| `cross_tenant_read` | Blocked (tenant isolation) |

Vulnerable path (`path=vulnerable` on `/run`): simulates unsafe decisions **without** broker enforcement (still no real execution).

```bash
make demo
```

## Validation matrix

| Check | Command | Notes |
|-------|---------|-------|
| Tests | `python -m pytest` | 50+ security-focused tests |
| Lint | `python -m ruff check .` | |
| Format | `python -m ruff format --check .` | |
| Types | `python -m mypy src tests` | Targets Python 3.12 |
| SAST | `python -m bandit -r src` | |
| Dependencies | `python -m pip_audit` | Requires network |
| Demo | `make demo` | |
| All (host) | `make validate` | Includes Docker if daemon up |
| Docker tests | `docker compose run --rm app python -m pytest` | Python 3.12 in container |

## API example

```bash
source .venv/bin/activate
uvicorn agent_control_plane.api:app --reload --port 8080
```

```bash
curl -s -X POST http://127.0.0.1:8080/run \
  -H 'Content-Type: application/json' \
  -d '{
    "request_id": "demo-1",
    "user_id": "user-1",
    "session_id": "sess-1",
    "tenant_id": "tenant-a",
    "role": "user",
    "user_message": "Read my records",
    "scenario": "safe_read",
    "path": "protected"
  }'
```

## Security doctrine (summary)

1. Deny by default; least privilege.
2. No model output is trusted.
3. Schema validation is not authorization.
4. The tool broker is the authority boundary.
5. Untrusted retrieved and user/web/email context cannot authorize tools.
6. External and destructive actions require human approval.
7. Output filtering and audit logging happen outside the model.
8. All tool execution is simulated in this lab.

Full doctrine: [PROJECT_DOCTRINE.md](PROJECT_DOCTRINE.md).

## Safe use

Use only in **authorized local lab** environments. Do not point this project at production systems, real customer data, or third-party targets. Report issues per [SECURITY.md](SECURITY.md).

## LinkedIn sharing blurb

I open-sourced a defensive lab that shows how to wrap tool-connected LLM agents in an external control plane: deny-by-default policy, broker authorization, provenance checks, human approval for high-impact tools, output filtering, and redacted audit logs. The model can ask; the broker decides. Simulated tools only, no real shell or exfiltration, tests for every control. Repo: llm-agent-control-plane-lab.

## Configuration

Copy `.env.example` to `.env` (optional). Policy: `policies/default.yaml`.

## Agent guidance

- [AGENTS.md](AGENTS.md)
- [.cursor/rules/](.cursor/rules/)

## License

MIT — [LICENSE](LICENSE).
