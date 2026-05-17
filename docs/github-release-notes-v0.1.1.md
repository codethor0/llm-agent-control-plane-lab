## Summary

Documentation and release-polish update. **No runtime or security control code changes.**

Adds a security controls matrix, architecture assets on the release tag, and social launch copy. Behavior matches v0.1.0.

## What changed

- **SECURITY-CONTROLS.md** — audit matrix (control, threat, implementation, tests, status, limitations)
- **Architecture assets** — `docs/assets/llm-agent-control-plane.svg` and `.png`
- **README** — embedded architecture diagram and links to static assets
- **Social launch docs** — `docs/social/` (LinkedIn, Hacker News, Substack blurb)
- **Release notes** — cleaned v0.1.0 text on GitHub (template header removed)

## What did not change

- No changes to `src/agent_control_plane/` security logic
- No policy weakening
- No test count reduction (still **83** tests)
- Simulated tools only; no production LLM API wiring

## Validation status

| Check | Result |
|-------|--------|
| pytest | 83 passed |
| ruff / mypy | pass |
| bandit | no issues |
| pip-audit | no known vulnerabilities |
| `scripts/validate_repo.py` | pass |
| docker compose pytest | 83 passed |
| make demo | pass |

## Safe use

Authorized local lab use only. See [SECURITY.md](https://github.com/codethor0/llm-agent-control-plane-lab/blob/main/SECURITY.md).

## Prior release

[v0.1.0](https://github.com/codethor0/llm-agent-control-plane-lab/releases/tag/v0.1.0) — first public defensive control plane lab release.

## Future work

See [ROADMAP.md](https://github.com/codethor0/llm-agent-control-plane-lab/blob/main/ROADMAP.md).
