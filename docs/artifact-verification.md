# Artifact Verification Guide

Use this guide to verify **llm-agent-control-plane** releases without trusting marketing claims. Every step states what is and is not proven.

## Before you start

- You need `git`, `sha256sum` (or `shasum -a 256` on macOS), and optionally the [GitHub CLI](https://cli.github.com/).
- **v0.2.7 and earlier** may not include `SHA256SUMS` on the release page. For those tags, use git and Actions verification only.

## 1. Download release artifacts

1. Open https://github.com/codethor0/llm-agent-control-plane/releases
2. Select the tag (for example `v0.2.8`).
3. Download assets when present:
   - `SHA256SUMS`
   - `llm-agent-control-plane-v0.2.8.tar.gz` (name matches tag)

If only source zipballs from GitHub UI are present, prefer the **automated** assets from the `release-artifacts` workflow when available. GitHub-generated zips may differ from `git archive` output.

## 2. Verify SHA256SUMS

```bash
cd /path/to/downloads
sha256sum -c SHA256SUMS
```

Expected: `OK` for each listed file.

**What this proves:** Downloaded files match the hashes published on the release.

**What this does not prove:** The publisher identity, absence of malware, or that CI passed. An attacker with release write access could upload matching hashes for malicious content.

## 3. Compare tag commit to release

```bash
git clone https://github.com/codethor0/llm-agent-control-plane.git
cd llm-agent-control-plane
git fetch --tags origin
git rev-parse v0.2.7^{commit}
```

On GitHub, open the release and confirm the tag points to the same commit hash.

**What this proves:** The tag name resolves to a specific commit.

**What this does not prove:** The commit was reviewed, signed, or built reproducibly.

## 4. Check GitHub Actions status

For the release commit:

```bash
gh run list --repo codethor0/llm-agent-control-plane --limit 15
```

Confirm successful runs (when triggered for that commit):

| Workflow | Confirms |
|----------|----------|
| CI | Lint, types, tests, bandit, pip-audit, Docker pytest |
| CodeQL | Python static analysis |
| Secret scan | Gitleaks |
| Trivy | Container CRITICAL/HIGH gate |
| SBOM | CycloneDX artifact produced |

```bash
gh run view <run-id> --repo codethor0/llm-agent-control-plane
```

**What this proves:** Documented checks passed in GitHub for that commit.

**What this does not prove:** Production safety, full CVE coverage, or signed artifacts.

## 5. Inspect SBOM artifact

1. Actions -> **SBOM** workflow -> green run for the release commit.
2. Download artifact **sbom-cyclonedx**.
3. Open `sbom.cyclonedx.json`.

Use the SBOM for inventory and license review. Combine with `pip-audit` / Dependabot for vulnerability awareness.

**Limitation:** SBOM is **unsigned** and generated at workflow time.

## 6. What cannot be verified yet

| Claim | Status |
|-------|--------|
| Cosign / sigstore signature on release files | Not available |
| GPG-signed git tags (project-wide requirement) | Not enforced |
| SLSA provenance attestation | Not generated |
| Reproducible byte-identical builds | Not claimed |
| Helm chart or container image on a registry | Not published by this repo |

Do not treat green CI as certification for regulated production without your own review.

## 7. How future signed releases should work

When signing is implemented, documentation will require:

1. Public key or sigstore identity for verification commands.
2. Which assets are signed (tarball, SBOM, container digest).
3. CI job that produces attestations without repository secrets beyond documented tokens.
4. Tests that fail if docs claim signing without workflow support.

Until then, use checksums + tag + CI + SBOM as **layered, unsigned** evidence.

## Related docs

- [release-provenance.md](release-provenance.md)
- [release-security-checklist.md](release-security-checklist.md)
- [supply-chain.md](supply-chain.md)
