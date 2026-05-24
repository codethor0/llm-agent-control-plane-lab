# Security scan status

Honest inventory of automated scanning for [llm-agent-control-plane](https://github.com/codethor0/llm-agent-control-plane). This document does **not** claim zero vulnerabilities or bug-free status.

Last reviewed: 2026-05-24 (pre public launch).

## Workflows (active)

| Workflow | Purpose |
|----------|---------|
| CI | pytest (293), ruff, mypy, bandit, pip-audit, repo/policy validators |
| CodeQL | Static analysis (Python) |
| Secret scan | Gitleaks |
| Trivy | Container image scan |
| SBOM | CycloneDX generation on PR/push |
| Release artifacts | Unsigned SHA256SUMS + tarball on `v*` tags |

## GitHub Advanced Security (API snapshot)

| Source | Status |
|--------|--------|
| Secret scanning alerts (open) | 0 |
| Dependabot alerts API | 403 — Dependabot alerts UI disabled for this repo |
| Repository vulnerability alerts | Enabled (`PUT .../vulnerability-alerts` returns 204) |
| CodeQL alerts (open on `main`) | See table below |

## Open CodeQL findings on `main`

CI and CodeQL **workflow jobs pass**; GitHub still lists **open** code scanning alerts from the default CodeQL suite. These are **maintainability / import-order** findings, not reported CVEs.

| Rule | Severity | Count (approx.) | Assessment |
|------|----------|-----------------|------------|
| `py/unsafe-cyclic-import` | error (CodeQL) | 8 | **Accepted limitation** for v0.2.9: `models`, `approval_tokens`, `policy_types`, and `provenance_integrity` use forward references and `model_rebuild`; runtime imports succeed and **293 tests pass**. Full cycle break is a post-release refactor. |
| `py/cyclic-import` | note | 2 | **Mitigated** on PR branch: `LLMAdapterMode` moved to `llm_adapter_mode.py` to break `config` ↔ `llm_adapter` cycle. Re-scan after merge. |
| `py/ineffectual-statement` | note | 1 | **False positive**: `...` body on `LLMAdapter` Protocol method (standard typing idiom). |

Do **not** dismiss alerts as "won't fix" without maintainer review. Post-release: refactor approval/model import graph or add targeted CodeQL query configuration after security review.

## pip-audit (dependency CVEs)

| Advisory | Package | Fix | Status |
|----------|---------|-----|--------|
| PYSEC-2026-161 | starlette 1.0.0 | >= 1.0.1 | **Fixed** on release branch via explicit `starlette>=1.0.1,<2` in `pyproject.toml` |

Re-run `python -m pip_audit` after `pip install -e ".[dev]"` on the merge commit.

## Trivy

Container scan runs in CI. Treat **HIGH/CRITICAL** image findings as release blockers unless documented with accepted risk. Latest PR CI runs reported success; inspect workflow logs for detail.

## What we do not claim

- No cosign, GPG-signed tags, or SLSA attestation
- No "zero vulnerabilities" while CodeQL or historical advisories exist
- Not a managed production platform

## Related docs

- [release-provenance.md](release-provenance.md)
- [supply-chain.md](supply-chain.md)
- [branch-protection.md](branch-protection.md)
- [commit-signing-guidance.md](commit-signing-guidance.md)
