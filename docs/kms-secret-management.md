# KMS and Secret Management Guidance

**Status:** Guidance only. **No cloud KMS integration is implemented** in this repository.

## Principles

1. **No secrets in the repository** — enforced by Gitleaks CI and [validate_repo.py](../scripts/validate_repo.py).
2. **No provider keys in committed config** — use `.env.example` with placeholders only.
3. **Runtime injection** — mount or fetch secrets at deploy time from enterprise KMS or secret manager.
4. **Least privilege** — separate keys for API auth, provenance HMAC, and future approval signing.

## Recommended KMS or secret manager patterns

| Secret type | Lab today | Enterprise target |
|-------------|-----------|-------------------|
| API keys | `ACP_ALLOWED_API_KEYS_FILE` | Secret manager volume or dynamic secret |
| Provenance HMAC | `ACP_PROVENANCE_HMAC_KEY_FILE` | KMS-backed key; rotation job |
| Approval signing (future) | Not implemented | Dedicated signing key in HSM/KMS |
| CI tokens | `GITHUB_TOKEN` only in Actions | Org-level secret management |

Patterns (vendor-neutral):

- **Mount secrets as files** — app reads path from env (current file-based pattern).
- **Sidecar refresh** — rotate files without image rebuild.
- **Envelope encryption** — data keys wrapped by KMS CMK for audit log encryption at rest (operator-owned).

Do not embed ARNs, vault paths, or credentials in this repo.

## Key rotation expectations

| Key | Rotation trigger | App behavior |
|-----|------------------|--------------|
| API keys | Quarterly or on incident | Support overlapping valid keys during cutover |
| Provenance HMAC | Policy change or annual | Re-sign provenance metadata; deny old signatures after grace |
| TLS certs | CA policy | Handled at ingress, not in app |

Document rotation runbooks outside this repository.

## HMAC provenance key storage

Strict provenance mode (`ACP_ENABLE_STRICT_PROVENANCE`) requires key bytes from `ACP_PROVENANCE_HMAC_KEY_FILE`. Lab uses fake test keys only. Production keys must never appear in git or container layers.

## API key storage

Production should avoid `ACP_API_KEY` inline env for multi-key fleets. Prefer secret manager files with restrictive POSIX permissions and no logging of values.

## Approval token signing key storage (future)

If persistent approvals add cryptographic signatures, store signing keys in KMS/HSM. **Not implemented.**

## CI secret handling

- GitHub Actions uses `GITHUB_TOKEN` for release artifact upload only ([github-actions-trust.md](github-actions-trust.md)).
- No repository secrets required for default workflows.
- Fork PRs use restricted tokens; review before merge.

## Local development limitations

Developers may use `.env` (gitignored) with **fake** keys from `.env.example`. Never use production keys locally. `validate_repo.py` blocks prompt artifacts and sensitive file patterns.

## Future tests needed

Before KMS integration claims:

- Config loads key from file path without logging content
- Missing or empty key fails closed in production profile
- Rotation: accept new key file with documented grace behavior (integration test with temp files only)

## Related docs

- [enterprise-integration-plan.md](enterprise-integration-plan.md)
- [deployment-boundaries.md](deployment-boundaries.md)
- [production-hardening.md](production-hardening.md)
