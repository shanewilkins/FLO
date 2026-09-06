"""Check committed canonical SPPM golden artifacts for byte drift."""

from __future__ import annotations

import argparse
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

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


def diagnostic_budget_violations(
    *, case: dict[str, object], diagnostics: Sequence[dict[str, object]]
) -> tuple[str, ...]:
    """Return deterministic violations of one case's reviewed warning budget."""
    case_id = str(case.get("id", "unknown"))
    raw_budget = case.get("diagnostic_budget")
    budget = raw_budget if isinstance(raw_budget, dict) else {}
    allowed_raw = budget.get("allowed")
    allowed = allowed_raw if isinstance(allowed_raw, dict) else {}
    violations: list[str] = []

    if diagnostics and not str(budget.get("rationale", "")).strip():
        violations.append(f"{case_id}: diagnostics require a reviewed rationale")

    by_code: dict[str, list[dict[str, object]]] = {}
    for diagnostic in diagnostics:
        code = str(diagnostic.get("code", "unknown"))
        by_code.setdefault(code, []).append(diagnostic)

    for code in sorted(by_code):
        code_budget = allowed.get(code)
        if not isinstance(code_budget, dict):
            violations.append(f"{case_id}: unexpected diagnostic code {code}")
            continue
        max_count = code_budget.get("max_count")
        if not isinstance(max_count, int) or max_count < 0:
            violations.append(f"{case_id}: {code} budget needs max_count >= 0")
        elif len(by_code[code]) > max_count:
            violations.append(
                f"{case_id}: {code} count {len(by_code[code])} exceeds {max_count}"
            )

        max_values = code_budget.get("max_values", {})
        if not isinstance(max_values, dict):
            violations.append(f"{case_id}: {code} max_values must be an object")
            continue
        for field, ceiling in sorted(max_values.items()):
            if not isinstance(ceiling, (int, float)) or isinstance(ceiling, bool):
                violations.append(f"{case_id}: {code}.{field} ceiling must be numeric")
                continue
            observed = [
                value
                for entry in by_code[code]
                if isinstance((value := entry.get(field)), (int, float))
                and not isinstance(value, bool)
            ]
            if observed and max(observed) > float(ceiling):
                violations.append(
                    f"{case_id}: {code}.{field} {max(observed):.2f} exceeds {float(ceiling):.2f}"
                )

    return tuple(violations)


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
        help="Committed golden artifact directory.",
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
        budget_violations: list[str] = []
        for case in cases:
            diagnostics = _build_case(case=case, outdir=generated_dir)
            budget_violations.extend(
                diagnostic_budget_violations(case=case, diagnostics=diagnostics)
            )
        drift = compare_baseline_dirs(
            expected_dir=baseline_dir,
            actual_dir=generated_dir,
            case_ids=case_ids,
        )

    if budget_violations:
        print("SPPM diagnostic budget exceeded.")
        for violation in budget_violations:
            print(f"  - {violation}")
        raise SystemExit(1)

    if drift.has_drift:
        _print_drift(drift)
        raise SystemExit(1)

    checked_count = len(_tracked_files_for_cases(baseline_dir, case_ids=case_ids))
    print(
        "SPPM golden artifact check passed: "
        f"{len(case_ids)} case(s), {checked_count} file(s) matched committed artifacts."
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
    wanted = set(case_ids or ())
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
    print("SPPM golden artifact drift detected.")
    if drift.missing_files:
        print("Missing committed golden files:")
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
