# GitHub Publication Readiness

Status as of commit `bcb3ff8` (pre-publication polish cycle pending new commit).

## Repository state

| Check | Status |
|-------|--------|
| Working tree clean | Yes (before this cycle's commit) |
| Git remote configured | No (intentional until user creates GitHub repo) |
| Latest commit | `bcb3ff8` — release readiness and prompt artifact hygiene |
| License | MIT |
| SECURITY.md / CONTRIBUTING.md / CODE_OF_CONDUCT.md | Present |

## Validation baseline (must re-run before push)

```bash
make validate
make demo
python scripts/validate_repo.py
```

Expected: 83 pytest passes, Docker pytest passes, repo hygiene OK.

## Publication artifacts

| Artifact | Location |
|----------|----------|
| Release checklist | [release-checklist.md](release-checklist.md) |
| v0.1.0 release notes draft | [github-release-notes-v0.1.0.md](github-release-notes-v0.1.0.md) |
| Roadmap | [ROADMAP.md](../ROADMAP.md) |
| Issue templates | `.github/ISSUE_TEMPLATE/` |
| PR template | `.github/pull_request_template.md` |

## Before first push

1. Create empty GitHub repository `llm-agent-control-plane-lab` (no README init if pushing existing history).
2. `git remote add origin git@github.com:OWNER/llm-agent-control-plane-lab.git`
3. `git push -u origin main`
4. Confirm GitHub Actions workflow passes on GitHub.
5. Update README CI badge with real `OWNER`.
6. Tag `v0.1.0` and publish release using `github-release-notes-v0.1.0.md`.

## Claims discipline

Do not describe this lab as:

- Production-ready for arbitrary deployments
- A guarantee against all prompt injection
- Certified or formally verified

Do describe it as:

- A defensive reference implementation
- Simulated tools only
- Test-backed controls with documented limitations
