from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "check_sppm_baseline_drift.py"

_spec = importlib.util.spec_from_file_location("sppm_baseline_drift", _SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Could not load baseline drift script from {_SCRIPT_PATH}")
_drift = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _drift
_spec.loader.exec_module(_drift)


def test_compare_baseline_dirs_reports_changed_missing_and_extra_files(tmp_path):
    expected_dir = tmp_path / "expected"
    actual_dir = tmp_path / "actual"
    (expected_dir / "case_a").mkdir(parents=True)
    (actual_dir / "case_a").mkdir(parents=True)
    (actual_dir / "case_b").mkdir(parents=True)

    (expected_dir / "case_a" / "render.svg").write_text("expected\n", encoding="utf-8")
    (expected_dir / "case_a" / "layout_result.json").write_text(
        "same\n", encoding="utf-8"
    )
    (expected_dir / "case_a" / "metadata.json").write_text(
        "missing\n", encoding="utf-8"
    )

    (actual_dir / "case_a" / "render.svg").write_text("actual\n", encoding="utf-8")
    (actual_dir / "case_a" / "layout_result.json").write_text(
        "same\n", encoding="utf-8"
    )
    (actual_dir / "case_b" / "metadata.json").write_text("extra\n", encoding="utf-8")

    drift = _drift.compare_baseline_dirs(
        expected_dir=expected_dir, actual_dir=actual_dir
    )

    assert drift.changed_files == ("case_a/render.svg",)
    assert drift.missing_files == ("case_a/metadata.json",)
    assert drift.extra_files == ("case_b/metadata.json",)
    assert drift.has_drift is True


def test_compare_baseline_dirs_limits_results_to_selected_case_ids(tmp_path):
    expected_dir = tmp_path / "expected"
    actual_dir = tmp_path / "actual"
    (expected_dir / "case_a").mkdir(parents=True)
    (expected_dir / "case_b").mkdir(parents=True)
    (actual_dir / "case_a").mkdir(parents=True)
    (actual_dir / "case_b").mkdir(parents=True)

    (expected_dir / "case_a" / "metadata.json").write_text("same\n", encoding="utf-8")
    (expected_dir / "case_b" / "metadata.json").write_text(
        "expected\n", encoding="utf-8"
    )
    (actual_dir / "case_a" / "metadata.json").write_text("same\n", encoding="utf-8")
    (actual_dir / "case_b" / "metadata.json").write_text("actual\n", encoding="utf-8")

    drift = _drift.compare_baseline_dirs(
        expected_dir=expected_dir,
        actual_dir=actual_dir,
        case_ids=("case_a",),
    )

    assert drift.changed_files == ()
    assert drift.missing_files == ()
    assert drift.extra_files == ()
    assert drift.has_drift is False


def test_committed_golden_cases_contain_only_canonical_artifacts() -> None:
    golden_root = _REPO_ROOT / "tests" / "golden" / "sppm"
    case_dirs = sorted(path for path in golden_root.iterdir() if path.is_dir())

    assert case_dirs
    for case_dir in case_dirs:
        artifacts = {path.name for path in case_dir.iterdir() if path.is_file()}
        assert artifacts == {"layout_result.json", "render.svg"}


def test_diagnostic_budget_rejects_unexpected_codes_and_threshold_growth() -> None:
    case = {
        "id": "reviewed",
        "diagnostic_budget": {
            "rationale": "Reviewed known geometry correction.",
            "allowed": {
                "known": {
                    "max_count": 1,
                    "max_values": {"distance_px": 10},
                }
            },
        },
    }
    diagnostics = (
        {"code": "known", "distance_px": 12},
        {"code": "known", "distance_px": 9},
        {"code": "new-warning"},
    )

    violations = _drift.diagnostic_budget_violations(
        case=case,
        diagnostics=diagnostics,
    )

    assert violations == (
        "reviewed: known count 2 exceeds 1",
        "reviewed: known.distance_px 12.00 exceeds 10.00",
        "reviewed: unexpected diagnostic code new-warning",
    )


def test_diagnostic_budget_requires_rationale_for_accepted_warning() -> None:
    violations = _drift.diagnostic_budget_violations(
        case={"id": "unreviewed"},
        diagnostics=({"code": "warning"},),
    )

    assert violations == (
        "unreviewed: diagnostics require a reviewed rationale",
        "unreviewed: unexpected diagnostic code warning",
    )
