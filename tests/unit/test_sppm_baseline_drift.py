from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


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


def test_committed_golden_hash_manifests_match_artifacts() -> None:
    golden_root = _REPO_ROOT / "tests" / "golden" / "sppm"
    case_dirs = sorted(path for path in golden_root.iterdir() if path.is_dir())

    assert case_dirs
    for case_dir in case_dirs:
        manifest = json.loads((case_dir / "sha256.json").read_text(encoding="utf-8"))
        expected_hashes = manifest["artifacts"]
        actual_hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(case_dir.iterdir())
            if path.is_file() and path.name != "sha256.json"
        }
        assert expected_hashes == actual_hashes
