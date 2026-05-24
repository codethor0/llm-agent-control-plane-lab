# Branch Protection Guidance

Recommended GitHub settings for `main` on [llm-agent-control-plane](https://github.com/codethor0/llm-agent-control-plane).

**Status:** This document is guidance only. As of the latest API check (`GET /repos/{owner}/{repo}/branches/main/protection`), **`main` is not protected** (HTTP 404). Enable protection in GitHub Settings before treating `main` as merge-gated.

## Recommended rules for `main`

| Setting | Recommendation | Rationale |
|---------|----------------|-----------|
| Require a pull request before merging | Enabled | Review before merge; aligns with P5/P6 PR workflow |
| Required approvals | 1 (or team policy) | Human review for security-sensitive repo |
| Dismiss stale pull request approvals when new commits are pushed | Enabled | Approvals match latest code |
| Require status checks to pass before merging | Enabled | CI and supply-chain gates |
| Require branches to be up to date before merging | Enabled (optional) | Reduces merge skew; may slow hotfixes |
| Restrict who can push to matching branches | Maintainers only | Prevents direct commits bypassing review |
| Allow force pushes | Disabled | Protects history |
| Allow deletions | Disabled | Prevents accidental branch deletion |
| Require linear history | Optional | Cleaner history vs merge commits tradeoff |
| Require signed commits | Optional | Improves authorship attestation; not required for lab |
| Require conversation resolution before merging | Enabled (optional) | Ensures review threads addressed |

## Required status checks (when workflows are enabled)

Add these as **required** checks after they have run at least once on a PR (GitHub only lists checks that have executed):

| Check / workflow | Job name (typical) |
|------------------|-------------------|
| CI | `validate`, `docker` |
| CodeQL | `Analyze Python` |
| Secret scan | `Gitleaks` |
| Trivy | `Container image scan` |
| SBOM | `Generate SBOM` |

Notes:

- CodeQL may take longer on first run; enable as required after green baseline.
- SBOM generation should pass even when it only uploads an artifact (no vuln gate).
- Dependabot does not add a status check; it opens update PRs.

## Tag and release protection

| Setting | Recommendation |
|---------|----------------|
| Protect release tags (`v*`) | Prefer rulesets or release workflow that only maintainers can create tags |
| GitHub Releases | Create from signed-off commits on `main` using [release-security-checklist.md](release-security-checklist.md) |

## What this does not provide

- Branch protection does not replace code review or threat modeling.
- Required checks only validate what workflows implement (bounded scans, not exhaustive assurance).
- Signed commits and linear history are organizational choices, not enabled by this repo automatically.

## Repository settings (verified via API)

| Setting | Value |
|---------|--------|
| `delete_branch_on_merge` | false (enable recommended) |
| GitHub Wiki | disabled (documentation lives in `docs/`) |
| Contributors API | `codethor0` only (web contributor graph may lag API) |

## Verification

After configuring protection in **Settings → Branches** (or Rulesets), confirm:

1. A direct push to `main` is rejected (if enforced).
2. A PR cannot merge until required checks are green.
3. Force-push to `main` is blocked.
