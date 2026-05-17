# Release Checklist

Use this checklist before tagging a public release or announcing the repository.

## Pre-release validation (host)

Requires Python 3.12 on PATH (`python3.12` or `make setup` after installing 3.12).

```bash
make setup
make validate
make demo
```

Expected:

- `check-python`: OK: Python 3.12.x
- ruff check and format: pass
- mypy: pass
- pytest: 83 passed
- `python scripts/validate_repo.py`: pass
- bandit: no issues in `src/`
- pip-audit: no known vulnerabilities (network required)
- docker compose build: pass (Docker daemon required)
- docker compose run --rm app python -m pytest: 83 passed

## Repo hygiene

- [ ] `.env` not committed
- [ ] `.venv/` not committed
- [ ] `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` not committed
- [ ] `audit_logs/` and `var/` not committed
- [ ] No prompt artifacts, master prompts, AI transcripts, Cursor chats, cycle reports, scratchpads, or validation notes staged or committed
- [ ] Only `.cursor/rules/*.mdc`, `PROJECT_DOCTRINE.md`, and `AGENTS.md` are committed as governance artifacts (not working prompts or chat exports)
- [ ] `python scripts/validate_repo.py` passes (also run via `make validate`)
- [ ] `.env.example` present with no secrets (force-add if global gitignore hides it)

## Security checks

- [ ] No real API keys, passwords, or tokens in the tree
- [ ] Test fixtures use clearly fake values only (`FAKE`, `example.invalid`)
- [ ] No jailbreak libraries or exploit instructions in docs
- [ ] `run_shell` disabled in policy; simulator does not execute shell
- [ ] No `subprocess`, `os.system`, or live HTTP client usage in `src/`
- [ ] Output filter and audit redaction tests pass
- [ ] Protected path tests pass; vulnerable path remains simulation-only

## Documentation accuracy

- [ ] README quick start commands work (`make setup && make demo`)
- [ ] README validation matrix matches `make validate` steps
- [ ] `docs/architecture.md` matches broker, policy, provenance, and approval flow
- [ ] `docs/defensive-controls.md` lists only tested controls
- [ ] `docs/provenance.md` states provenance is declarative, not attested
- [ ] Claims avoid unsupported words like "production-ready" or "unhackable"

## Docker checks

- [ ] `docker compose build` succeeds
- [ ] `docker compose run --rm app python -m pytest` passes
- [ ] Image uses `python:3.12-slim-bookworm`
- [ ] No bind mounts required for CI-equivalent test run

## GitHub checks

- [ ] `LICENSE` is MIT
- [ ] `SECURITY.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` present
- [ ] `ROADMAP.md` and `docs/github-release-notes-v0.1.0.md` present
- [ ] `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md` present
- [ ] GitHub Actions workflow uses `permissions: contents: read` and Python 3.12
- [ ] CI badge URL updated with real `OWNER/repo` (see README publication status)
- [ ] Remote configured: `git remote add origin <url>` and initial push
- [ ] See [github-publication-readiness.md](github-publication-readiness.md)

## First public release

- [ ] Tag release (example: `v0.1.0`)
- [ ] GitHub release notes summarize scope: defensive lab, simulated tools only
- [ ] Verify CI green on `main` after push
- [ ] Confirm issue templates or discussion guidelines if enabling community feedback

## LinkedIn sharing checklist

- [ ] Link to public repository URL (not a local path)
- [ ] State "reference lab" and "simulated tools only"
- [ ] Mention broker, policy, provenance, approval, output filter, audit
- [ ] Do not claim production certification or universal LLM safety
- [ ] Optional: use README "LinkedIn sharing blurb" as a starting point
