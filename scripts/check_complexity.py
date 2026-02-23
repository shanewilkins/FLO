#!/usr/bin/env python3
"""Check cyclomatic complexity for Python files using radon.

Exits with non-zero when any function/class has complexity > threshold.
Designed to be run from pre-commit or CI.
"""
from __future__ import annotations

import sys
import pathlib
from typing import Sequence

try:
    from radon.complexity import cc_visit
except Exception:  # pragma: no cover - missing optional dep
    print("radon is required to run complexity checks. Install dev deps.")
    raise


THRESHOLD = 15


def check_files(files: Sequence[pathlib.Path]) -> int:
    """Check `files` for cyclomatic complexity above threshold.

    Returns zero on success or non-zero error code on failure.
    """
    problems = []
    for p in files:
        try:
            src = p.read_text()
        except Exception:
            continue
        blocks = cc_visit(src)
        for b in blocks:
            if getattr(b, "complexity", 0) > THRESHOLD:
                problems.append((p, b.name, b.lineno, b.complexity))

    if problems:
        print("Complexity threshold exceeded (>{}). Detected:".format(THRESHOLD))
        for p, name, lineno, complexity in problems:
            print(f"{p}:{lineno}: {name} complexity={complexity}")
        return 2
    print("Complexity check passed.")
    return 0


def gather_files(args: Sequence[str]) -> list[pathlib.Path]:
    """Return a list of python files to analyze.

    If `args` is non-empty, filter provided paths, otherwise search the
    project's `src` directory for Python files.
    """
    if args:
        return [pathlib.Path(a) for a in args if a.endswith(".py")]
    # default: check all project python files under src
    base = pathlib.Path(__file__).resolve().parents[1] / "src"
    return [p for p in base.rglob("*.py")]


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entrypoint for complexity checks.

    Accepts an optional argv list for programmatic invocation.
    """
    argv = list(argv or sys.argv[1:])
    files = gather_files(argv)
    return check_files(files)


if __name__ == "__main__":
    raise SystemExit(main())
