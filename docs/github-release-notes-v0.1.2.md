## Summary

Docs-only release marking the **final end-to-end verification** state on `main`. No runtime or security control code changes.

This tag includes the hygiene-scanner fix for pytest basetemp directories, **84** passing tests, fresh-clone verification, and aligned documentation. Prior tags `v0.1.0` and `v0.1.1` are unchanged.

## What changed since v0.1.1

- **Fresh clone verified** — `git clone`, `make setup`, pytest, `scripts/validate_repo.py`, and `make demo` succeed on a clean checkout
- **Repo hygiene scanner** — skip `pytest-of-*` basetemp paths to avoid false positives from test fixtures (regression test added)
- **Test count** — 84 tests (includes `test_ignored_pytest_basetemp_paths_do_not_fail`)
- **Documentation** — test counts and social launch copy aligned to v0.1.2 narrative

## What did not change

- No changes to `src/agent_control_plane/` security logic
- No policy weakening
- Simulated tools only; no production LLM API wiring
- `v0.1.0` and `v0.1.1` tags were not moved or retagged

## Validation status

| Check | Result |
|-------|--------|
| pytest | 84 passed |
| ruff / mypy | pass |
| bandit | no issues |
| pip-audit | no known vulnerabilities |
| `scripts/validate_repo.py` | pass |
| docker compose pytest | 84 passed |
| make demo | 7 scenarios OK |
| GitHub Actions on `main` | green |
| Fresh clone E2E | pass |
| API `GET /health` | 200 |
| API `POST /run` (safe_read) | 200, allowed |

## Safe use

Authorized local lab use only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane-lab/blob/main/SECURITY.md).

## Known limitations

- Provenance is declarative metadata, not signed or cryptographically attested ([provenance.md](https://github.com/codethor0/llm-agent-control-plane-lab/blob/main/docs/provenance.md))
- Simulated model only (scenario-driven; no live LLM API by default)
- Architecture PNG regeneration uses local tooling (not in CI)
- Multi-tenant isolation is demonstration-level

## Prior releases

- [v0.1.1](https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.1) — documentation and architecture assets
- [v0.1.0](https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.0) — initial public release

## Future work

See [ROADMAP.md](https://github.com/codethor0/llm-agent-control-plane-lab/blob/main/ROADMAP.md).
