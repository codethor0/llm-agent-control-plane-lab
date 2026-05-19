# Release Provenance

This document describes **release trust** for **llm-agent-control-plane**: what consumers can verify today, what is not yet signed, and how maintainers should publish future releases.

**Scope:** Open-source release hygiene and artifact checksums. This is **not** SLSA certification, not a managed production platform, and not cryptographic proof that binaries are safe to run.

## What release provenance means here

Release provenance answers:

1. **Which commit** does a release tag point to?
2. **Which CI workflows** ran on that commit before the tag?
3. **Which supply-chain artifacts** (SBOM, scans) exist for that commit?
4. **Which downloadable files** belong to the release, and do their checksums match?

The control plane runtime (`src/agent_control_plane/`) is unchanged by release provenance work. Provenance here is about **the repository and its release pipeline**, not tool-call provenance inside the agent (see [provenance.md](provenance.md)).

## What is currently verified

| Control | Mechanism | Signed? |
|---------|-----------|---------|
| Tests and lint | CI workflow on `main` / PRs | N/A |
| Static analysis | CodeQL on push/PR | N/A |
| Secret scan | Gitleaks (full history) | N/A |
| Container CVE scan | Trivy on built image (no registry push) | N/A |
| Dependency inventory | CycloneDX SBOM artifact from SBOM workflow | **No** |
| Tag-to-commit binding | Annotated git tag on GitHub | Git tag only (not GPG/cosign by default) |
| Source archive checksums | `release-artifacts` workflow on tag push (from P12) | **Checksum only** (SHA-256, not signature) |

Green CI on the release commit is required project practice before tagging. See [release-security-checklist.md](release-security-checklist.md).

## What is not yet signed

- **Git tags** are not required to be GPG-signed by maintainers.
- **GitHub Releases** are not cosign/sigstore-attested in this repository.
- **SBOM** (`sbom.cyclonedx.json`) is uploaded unsigned.
- **SHA256SUMS** files are integrity checksums only; they are **not** digital signatures.
- **No SLSA provenance generator** is configured; do not claim SLSA Level 1+ unless a future workflow implements and documents it.

Releases before the `release-artifacts` workflow (including **v0.2.7**) may have **no** automated `SHA256SUMS` on the release page. Verify those tags using git and CI history only.

## How to verify tags

```bash
git fetch --tags origin
git show v0.2.7
git rev-parse v0.2.7^{commit}
```

Confirm the commit matches the release notes and the commit you expect on `main`. Compare with GitHub: **Releases** -> tag -> target commit.

Annotated tags are preferred:

```bash
git cat-file -p v0.2.7
```

## How to verify GitHub Actions runs

1. Open the repository **Actions** tab.
2. Find workflows for the **release commit** (the parent of the tag, or the README commit if you tag after README update).
3. Confirm green runs for: **CI**, **CodeQL**, **Secret scan**, **Trivy**, **SBOM**.

Use the CLI:

```bash
gh run list --repo codethor0/llm-agent-control-plane --branch main --limit 20
gh run view <run-id> --repo codethor0/llm-agent-control-plane
```

Workflow conclusions are authoritative; local `make validate` does not replace CI for release gating.

## How to verify SBOM artifacts

1. Open a green **SBOM** workflow run for the release commit.
2. Download artifact **`sbom-cyclonedx`**.
3. Inspect `sbom.cyclonedx.json` (CycloneDX JSON).

The SBOM lists components at generation time. It is not a vulnerability report and is **not signed**. See [artifact-verification.md](artifact-verification.md).

## How to verify checksums (when generated)

For releases published **after** the `release-artifacts` workflow is on `main`:

1. On the GitHub **Release** page, download `SHA256SUMS` and the matching `llm-agent-control-plane-<tag>.tar.gz`.
2. Verify:

```bash
sha256sum -c SHA256SUMS
```

3. Optionally reproduce the archive locally:

```bash
git fetch --tags origin
git checkout <tag>
git archive --format=tar.gz --output=llm-agent-control-plane-<tag>.tar.gz HEAD
sha256sum llm-agent-control-plane-<tag>.tar.gz
```

Compare the digest to the line in `SHA256SUMS`.

Checksums prove **file integrity** after download. They do **not** prove who built the file unless combined with signed tags or sigstore in a future phase.

## Operator trust assumptions

Consumers trust:

- GitHub as host for source, Actions, and Releases
- Repository maintainers to tag only after green CI
- GitHub-provided `GITHUB_TOKEN` for automated release uploads (no custom secrets in the checksum workflow)

Consumers should **not** assume:

- Releases are cosign-signed
- SBOM or checksum files are tamper-evident against a compromised maintainer account
- Passing scans mean absence of vulnerabilities

## Limitations

- Point-in-time scans; new CVEs may appear after a green run.
- Checksum workflow does not sign containers or publish images.
- Manual release steps (notes, README version) can drift from automation if not followed.
- Forks and mirrors are outside this project's release trust boundary.

## Future signing roadmap

| Phase | Goal | Status |
|-------|------|--------|
| P12 (this) | Document trust model; SHA256SUMS on tag; verification guides | In progress |
| Next | Optional GPG-signed tags for maintainers | Not implemented |
| Next | cosign/sigstore for release assets or container images | Not implemented |
| Next | SLSA provenance generator aligned to documented level | Not implemented |
| Next | Pin all Actions to full commit SHAs with documented update process | Optional; see [github-actions-trust.md](github-actions-trust.md) |

## Related documentation

- [artifact-verification.md](artifact-verification.md) — step-by-step verification
- [release-security-checklist.md](release-security-checklist.md) — maintainer checklist
- [supply-chain.md](supply-chain.md) — CI workflows overview
- [github-actions-trust.md](github-actions-trust.md) — Actions pinning and maintenance
