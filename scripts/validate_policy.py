#!/usr/bin/env python3
"""Validate policy schema/invariants and compare canonical SHA-256 to golden hash."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = REPO_ROOT / "policies" / "default.yaml"
DEFAULT_HASH = REPO_ROOT / "policies" / "default.sha256"


def _repo_src_on_path() -> None:
    src = REPO_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate policy integrity and SHA-256 hash.")
    parser.add_argument(
        "--policy",
        type=Path,
        default=DEFAULT_POLICY,
        help=f"Policy YAML path (default: {DEFAULT_POLICY})",
    )
    parser.add_argument(
        "--hash-file",
        type=Path,
        default=DEFAULT_HASH,
        help=f"Expected SHA-256 file (default: {DEFAULT_HASH})",
    )
    parser.add_argument(
        "--write-hash",
        action="store_true",
        help="Write computed hash to --hash-file (use when policy changes intentionally)",
    )
    args = parser.parse_args()

    _repo_src_on_path()
    from agent_control_plane.policy_integrity import (  # noqa: PLC0415
        PolicyIntegrityError,
        validate_policy_file,
        verify_policy_file_hash,
    )

    policy_path = args.policy.resolve()
    hash_path = args.hash_file.resolve()

    try:
        digest = validate_policy_file(policy_path)
    except PolicyIntegrityError as exc:
        print(f"FAIL: policy validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"OK: policy schema and invariants valid ({policy_path})")
    print(f"     canonical SHA-256: {digest}")

    if args.write_hash:
        hash_path.write_text(f"{digest}\n", encoding="utf-8")
        print(f"OK: wrote hash to {hash_path}")
        return 0

    try:
        verify_policy_file_hash(policy_path, hash_path)
    except PolicyIntegrityError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        print(
            "Hint: if the policy changed intentionally, run "
            "python scripts/validate_policy.py --write-hash",
            file=sys.stderr,
        )
        return 1

    print(f"OK: hash matches {hash_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
