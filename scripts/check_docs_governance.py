#!/usr/bin/env python3
"""Warn about documentation-governance drift.

This script is intentionally warning-first. By default it prints warnings and
returns success so contributors see likely governance issues without blocking
unrelated work. Use ``--strict`` to fail on warnings.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]


def _repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def _iter_targets(raw_paths: list[str]) -> list[Path]:
    if raw_paths:
        return [REPO_ROOT / raw for raw in raw_paths]

    targets: list[Path] = []
    for pattern in (
        "docs/**/*.md",
        "examples/**/*.flo",
        "schema/*.json",
        "README.md",
        "src/flo/services/errors.py",
    ):
        targets.extend(sorted(REPO_ROOT.glob(pattern)))
    return targets


def _has_status_header(path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return True
    head = lines[:12]
    return any(line.startswith("Status:") for line in head)


def _warn_design_status(targets: Iterable[Path], warnings: list[str]) -> None:
    for path in targets:
        rel = _repo_relative(path)
        if rel.suffix != ".md":
            continue
        if rel.parts[:2] != ("docs", "design"):
            continue
        if rel.name == "README.md":
            continue
        if not _has_status_header(path):
            warnings.append(f"{rel}: design doc is missing a top-level Status header")


def _warn_known_files(targets: Iterable[Path], warnings: list[str]) -> None:
    for path in targets:
        rel = _repo_relative(path)
        if rel == Path("docs/CLI_Error_Contract.md"):
            warnings.append(
                "docs/CLI_Error_Contract.md: interface-style contract lives at docs/ top level; "
                "confirm this is intentional or move/mirror normative parts under docs/specs/"
            )


def _warn_cross_file_drift(targets: Iterable[Path], warnings: list[str]) -> None:
    rels = {_repo_relative(path) for path in targets}

    schema_changed = any(rel.parts and rel.parts[0] == "schema" for rel in rels)
    specs_changed = any(rel.parts[:2] == ("docs", "specs") for rel in rels)
    policy_changed = any(rel.parts[:2] == ("docs", "policy") for rel in rels)
    errors_changed = Path("src/flo/services/errors.py") in rels
    cli_contract_changed = Path("docs/specs/cli_error_contract.md") in rels

    if schema_changed and not (specs_changed or policy_changed):
        warnings.append(
            "schema/ changed without docs/specs/ or docs/policy/ in the same change; "
            "check whether normative docs need an update"
        )

    if errors_changed and not cli_contract_changed:
        warnings.append(
            "src/flo/services/errors.py changed without docs/specs/cli_error_contract.md; "
            "check whether the CLI contract doc needs a sync update"
        )


def main() -> int:
    """Check documentation governance and return a status code."""
    parser = argparse.ArgumentParser(prog="check_docs_governance.py")
    parser.add_argument(
        "--strict", action="store_true", help="fail when warnings are emitted"
    )
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    targets = _iter_targets(args.paths)
    warnings: list[str] = []

    _warn_design_status(targets, warnings)
    _warn_known_files(targets, warnings)
    _warn_cross_file_drift(targets, warnings)

    if not warnings:
        print("Documentation governance check passed.")
        return 0

    for warning in warnings:
        print(f"WARN  {warning}")

    if args.strict:
        print(f"Documentation governance check failed with {len(warnings)} warning(s).")
        return 2

    print(f"Documentation governance check completed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
