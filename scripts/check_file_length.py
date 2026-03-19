#!/usr/bin/env python3
"""Check Python file lengths with warning and fail thresholds.

Warns when a file exceeds --warn-lines and fails when it exceeds --fail-lines.
Designed for use in pre-commit and CI.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections.abc import Sequence


DEFAULT_WARN_LINES = 500
DEFAULT_FAIL_LINES = 750


def _line_count(path: pathlib.Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _gather_python_files(argv: Sequence[str]) -> list[pathlib.Path]:
    if argv:
        return [pathlib.Path(raw) for raw in argv if raw.endswith(".py")]

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    roots = [repo_root / "src", repo_root / "tests", repo_root / "scripts"]

    files: list[pathlib.Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(sorted(root.rglob("*.py")))
    return files


def _check_lengths(files: Sequence[pathlib.Path], warn_lines: int, fail_lines: int) -> int:
    warnings: list[tuple[pathlib.Path, int]] = []
    failures: list[tuple[pathlib.Path, int]] = []

    for path in files:
        count = _line_count(path)
        if count > fail_lines:
            failures.append((path, count))
        elif count > warn_lines:
            warnings.append((path, count))

    warnings.sort(key=lambda item: item[1], reverse=True)
    failures.sort(key=lambda item: item[1], reverse=True)

    for path, count in warnings:
        print(f"WARN  {path}:{count} lines (>{warn_lines})")

    for path, count in failures:
        print(f"FAIL  {path}:{count} lines (>{fail_lines})")

    if failures:
        print(
            f"File length check failed: {len(failures)} file(s) exceed {fail_lines} lines."
        )
        return 2

    print("File length check passed.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the file-length check from CLI arguments."""
    parser = argparse.ArgumentParser(prog="check_file_length.py")
    parser.add_argument("--warn-lines", type=int, default=DEFAULT_WARN_LINES)
    parser.add_argument("--fail-lines", type=int, default=DEFAULT_FAIL_LINES)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    if args.warn_lines < 0 or args.fail_lines < 0:
        print("warn-lines and fail-lines must be >= 0")
        return 2
    if args.warn_lines >= args.fail_lines:
        print("warn-lines must be less than fail-lines")
        return 2

    files = _gather_python_files(args.files)
    return _check_lengths(files, warn_lines=args.warn_lines, fail_lines=args.fail_lines)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
