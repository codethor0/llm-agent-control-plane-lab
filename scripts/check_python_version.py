#!/usr/bin/env python3
"""Fail unless the active interpreter is Python 3.12.x (project target)."""

import sys


def main() -> None:
    major, minor = sys.version_info.major, sys.version_info.minor
    if major != 3 or minor != 12:
        print(
            f"ERROR: Expected Python 3.12.x for this project, got {sys.version.split()[0]}.",
            file=sys.stderr,
        )
        print(
            "Use pyenv, asdf, or Docker (see README). Python 3.14+ is a local mismatch only.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(f"OK: Python {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
