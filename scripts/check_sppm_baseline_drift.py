"""Local-only check for canonical SPPM baseline artifact drift.

Baseline render artifacts live under ``renders/`` and are intentionally ignored
by git, so this script is for developer-managed local regression review rather
than remote CI enforcement.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import tempfile
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_sppm_baseline_artifacts import (  # noqa: E402
    DEFAULT_MANIFEST,
    DEFAULT_OUTDIR,
    _build_case,
    _filter_cases,
    _load_cases,
    _resolve_repo_path,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DriftSummary:
    missing_files: tuple[str, ...]
    extra_files: tuple[str, ...]
    changed_files: tuple[str, ...]

    @property
    def has_drift(self) -> bool:
        return bool(self.missing_files or self.extra_files or self.changed_files)


def main() -> int:
    parser = argparse.ArgumentParser(prog="check_sppm_baseline_drift.py")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to JSON corpus manifest.",
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help="Local baseline artifact directory.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Optional case id to validate. Repeat to limit the drift check to a subset.",
    )
    args = parser.parse_args()

    manifest_path = _resolve_repo_path(args.manifest)
    baseline_dir = _resolve_repo_path(args.baseline_dir)
    cases = _filter_cases(_load_cases(manifest_path), case_ids=args.case_id)
    case_ids = tuple(str(case["id"]) for case in cases)

    with tempfile.TemporaryDirectory(prefix="flo-sppm-baseline-") as temp_dir:
        generated_dir = Path(temp_dir) / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            _build_case(case=case, outdir=generated_dir)
        drift = compare_baseline_dirs(
            expected_dir=baseline_dir,
            actual_dir=generated_dir,
            case_ids=case_ids,
        )

    if drift.has_drift:
        _print_drift(drift)
        raise SystemExit(1)

    checked_count = len(_tracked_files_for_cases(baseline_dir, case_ids=case_ids))
    print(
        "SPPM baseline drift check passed: "
        f"{len(case_ids)} case(s), {checked_count} file(s) matched local artifacts."
    )
    return 0


def compare_baseline_dirs(
    *,
    expected_dir: Path,
    actual_dir: Path,
    case_ids: Sequence[str] | None = None,
) -> DriftSummary:
    expected_files = _tracked_files_for_cases(expected_dir, case_ids=case_ids)
    actual_files = _tracked_files_for_cases(actual_dir, case_ids=case_ids)

    expected_keys = set(expected_files)
    actual_keys = set(actual_files)
    missing_files = tuple(sorted(expected_keys.difference(actual_keys)))
    extra_files = tuple(sorted(actual_keys.difference(expected_keys)))

    changed_files = tuple(
        sorted(
            relative_path
            for relative_path in expected_keys.intersection(actual_keys)
            if expected_files[relative_path].read_bytes()
            != actual_files[relative_path].read_bytes()
        )
    )
    return DriftSummary(
        missing_files=missing_files,
        extra_files=extra_files,
        changed_files=changed_files,
    )


def _tracked_files_for_cases(
    root_dir: Path,
    *,
    case_ids: Sequence[str] | None = None,
) -> dict[str, Path]:
    wanted = {case_id for case_id in case_ids or ()}
    tracked: dict[str, Path] = {}
    if not root_dir.exists():
        return tracked
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root_dir).as_posix()
        case_id = relative_path.split("/", 1)[0]
        if wanted and case_id not in wanted:
            continue
        tracked[relative_path] = path
    return tracked


def _print_drift(drift: DriftSummary) -> None:
    print("SPPM baseline drift detected.")
    if drift.missing_files:
        print("Missing local baseline files:")
        for relative_path in drift.missing_files:
            print(f"  - {relative_path}")
    if drift.extra_files:
        print("Unexpected generated files:")
        for relative_path in drift.extra_files:
            print(f"  - {relative_path}")
    if drift.changed_files:
        print("Changed files:")
        for relative_path in drift.changed_files:
            print(f"  - {relative_path}")


if __name__ == "__main__":
    raise SystemExit(main())