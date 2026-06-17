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
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED_FILES = {
    "src/flo/render/layout_core/elk.py",
    "src/flo/render/layout_core/elk_sppm_helpers.py",
    "src/flo/render/_svg_sppm_rows.py",
}


def _normalized(path: pathlib.Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix().lstrip("./")


def _is_excluded(path: pathlib.Path) -> bool:
    normalized = _normalized(path)
    return normalized.startswith("scripts/") or normalized in EXCLUDED_FILES


def check_files(files: Sequence[pathlib.Path]) -> int:
    """Check `files` for cyclomatic complexity above threshold.

    Returns zero on success or non-zero error code on failure.
    """
    problems = []
    for p in files:
        if _is_excluded(p):
            continue
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
        files = [pathlib.Path(a) for a in args if a.endswith(".py")]
        return [path for path in files if not _is_excluded(path)]
    # default: check all project python files under src
    base = REPO_ROOT / "src"
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
