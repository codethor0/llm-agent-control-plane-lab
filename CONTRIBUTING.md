# Contributing

Thank you for helping improve this defensive reference implementation.

## Before you start

1. Read [SECURITY-CONTROLS.md](SECURITY-CONTROLS.md) and [docs/defensive-controls.md](docs/defensive-controls.md).
2. Run `make setup` then `make validate` on `main` to confirm a clean baseline.

## Pull requests

- One logical change per PR when possible.
- Every security control change includes tests that state the invariant in the test name.
- Do not weaken, skip, or remove security tests to pass CI.
- No emojis in code, documentation, or commit messages.
- No real secrets, shell execution from model paths, or live external API calls.

## Code standards

- Python 3.12, formatted with ruff, typed with mypy strict on `src` and `tests`.
- Public functions: type hints. Security-sensitive functions: docstring stating the invariant.
- Run `make validate` before opening a PR.

## Documentation

Update `docs/` when behavior or architecture changes. Keep README commands copy-paste accurate.

Internal build-process files (IDE metadata, agent instruction exports, master prompts) belong outside the public repository. Public security principles live in [SECURITY-CONTROLS.md](SECURITY-CONTROLS.md) and [docs/defensive-controls.md](docs/defensive-controls.md).

## Conduct

See `CODE_OF_CONDUCT.md`.
