from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from flo.render._diagnostics import RenderDiagnostic, RenderDiagnosticsReport


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "run_sppm_strategy_matrix.py"

_spec = importlib.util.spec_from_file_location("sppm_matrix", _SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Could not load strategy matrix script from {_SCRIPT_PATH}")
_matrix = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _matrix
_spec.loader.exec_module(_matrix)


def test_invariant_diagnostics_clean_flags_error_and_partial_output():
    report = RenderDiagnosticsReport(
        diagram="sppm",
        backend="elk",
        artifact_kind="layout_result",
        error_count=1,
        partial_output=True,
        summary="1 error(s), 1 warning(s) while rendering sppm via elk",
    )

    failures = _matrix._invariant_diagnostics_clean(report, case_id="demo_case")

    assert len(failures) == 2
    assert "diagnostics_error case=demo_case error_count=1" in failures
    assert "diagnostics_partial_output case=demo_case" in failures[1]


def test_diagnostic_warning_burden_prefers_advisory_over_geometry_loss():
    report = RenderDiagnosticsReport(
        diagram="sppm",
        backend="elk",
        artifact_kind="layout_result",
        category_counts={
            "missing_geometry": 1,
            "lossy_recovery": 2,
            "uncategorized": 3,
        },
    )

    burden = _matrix._diagnostic_warning_burden(report)

    # 1*3 + 2*2 + 3*1
    assert burden == 10.0


def test_evaluate_case_captures_diagnostic_secondary_metrics(monkeypatch):
    strategy = _matrix.Strategy(
        partition_mode="chain_progressive",
        port_constraints="fixed_order",
        helper_anchors="off",
        spacing_profile="balanced",
    )

    base_result = _matrix.LayoutResult(
        orientation="lr",
        canvas_bounds=_matrix.LayoutBounds(
            x_px=0.0, y_px=0.0, width_px=100.0, height_px=50.0
        ),
        node_bounds={},
        edge_paths={},
        diagnostics=(
            RenderDiagnostic(
                code="elk-edge-missing",
                severity="warning",
                message="ELK response did not normalize requested edge 'a->b'.",
            ),
        ),
    )

    class _FakeOptions:
        layout_fit = "fit"

    def fake_request_and_result(_case):
        return (
            _matrix.ElkLayoutRequest(
                diagram="sppm",
                direction="RIGHT",
                lanes=(),
                nodes=(),
                edges=(),
            ),
            base_result,
            _FakeOptions(),
        )

    monkeypatch.setattr(_matrix, "_request_and_result", fake_request_and_result)

    case = {"id": "demo", "input": "examples/reference/linear.flo", "options": {}}
    result = _matrix._evaluate_case(case=case, strategy=strategy)

    assert result.passed is False
    assert result.diagnostic_warning_count == 1
    assert result.diagnostic_error_count == 0
    assert result.diagnostic_warning_burden == 3.0
    assert result.partial_output is True
    assert any(
        current.startswith("diagnostics_partial_output") for current in result.failures
    )
