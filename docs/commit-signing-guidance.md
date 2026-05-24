# Commit and tag signing guidance

This repository does **not** require signed commits or tags today. Release artifacts use **unsigned** SHA256 checksums only (see [release-provenance.md](release-provenance.md)).

## Current status

| Item | Status |
|------|--------|
| Git commit signatures (GPG/SSH) | Not required; verify with `git log --show-signature` |
| Annotated tags | `v0.2.9` tag exists; not cryptographically signed |
| GitHub verified commits | Optional; configure on maintainer account |
| Release tarball signing | Not implemented (no cosign, no GPG release signatures) |

## Optional: sign future commits locally

1. Generate a GPG or SSH signing key **outside** this repository.
2. Add the public key to your GitHub account (Settings → SSH and GPG keys).
3. Configure Git locally, for example:
   - `git config --global user.signingkey <KEY_ID>`
   - `git config --global commit.gpgsign true`
4. Sign annotated release tags: `git tag -s vX.Y.Z -m "vX.Y.Z: summary"`

Do not commit private keys, passphrases, or key material to the repository.

## Release trust model

Consumers should verify:

- Tag points to a green `main` commit with required checks (see [branch-protection.md](branch-protection.md)).
- CI workflows (CodeQL, Gitleaks, Trivy, SBOM) passed on the release commit.
- `SHA256SUMS` matches the downloaded tarball (integrity only, not publisher identity).
