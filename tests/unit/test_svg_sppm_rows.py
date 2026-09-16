from __future__ import annotations

from types import SimpleNamespace

from flo.render.layout_core.models import LayoutBounds, LayoutPoint, RoutedEdgePath
from flo.render.sppm.rows import (
    _apply_edge_shifts,
    rework_alignment_diagnostics,
    row_gap_diagnostics,
)


def test_apply_edge_shifts_rebuilds_distinct_branch_and_return_routes() -> None:
    node_bounds = {
        "decision": LayoutBounds(x_px=100.0, y_px=20.0, width_px=120.0, height_px=80.0),
        "correction": LayoutBounds(
            x_px=110.0, y_px=180.0, width_px=100.0, height_px=60.0
        ),
    }
    stale_points = (
        LayoutPoint(x_px=40.0, y_px=100.0),
        LayoutPoint(x_px=40.0, y_px=400.0),
        LayoutPoint(x_px=160.0, y_px=400.0),
    )
    edge_paths = {
        ("decision", "correction"): RoutedEdgePath(
            edge=("decision", "correction"),
            points=stale_points,
            label="yes",
            is_rework=False,
            rework_variant="branch",
        ),
        ("correction", "decision"): RoutedEdgePath(
            edge=("correction", "decision"),
            points=tuple(reversed(stale_points)),
            label="Recheck",
            is_rework=True,
            rework_variant="return",
        ),
    }

    shifted = _apply_edge_shifts(
        edge_paths=edge_paths,
        shifts={},
        node_bounds=node_bounds,
    )

    branch = shifted[("decision", "correction")]
    rework_return = shifted[("correction", "decision")]
    assert branch.is_rework is False
    assert max(point.y_px for point in branch.points) <= 210.0
    assert branch.points[-1] == LayoutPoint(x_px=110.0, y_px=210.0)
    assert rework_return.is_rework is True
    assert max(point.x_px for point in rework_return.points) > 220.0
    assert rework_return.points[-1] == LayoutPoint(x_px=160.0, y_px=20.0)


def test_row_gap_diagnostics_warns_when_rows_are_too_close() -> None:
    node_bounds = {
        "mainline": LayoutBounds(x_px=40.0, y_px=20.0, width_px=120.0, height_px=80.0),
        "rework": LayoutBounds(x_px=40.0, y_px=130.0, width_px=120.0, height_px=80.0),
    }
    lanes = (
        SimpleNamespace(id="__sppm_row_mainline", node_ids=("mainline",)),
        SimpleNamespace(id="__sppm_row_rework", node_ids=("rework",)),
    )

    diagnostics = row_gap_diagnostics(
        node_bounds=node_bounds,
        lanes=lanes,
        edge_paths={},
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "sppm-row-gap-tight"
    assert diagnostics[0].metadata["measured_gap_px"] == 30.0


def test_row_gap_diagnostics_returns_empty_when_gap_is_sufficient() -> None:
    node_bounds = {
        "mainline": LayoutBounds(x_px=40.0, y_px=20.0, width_px=120.0, height_px=80.0),
        "rework": LayoutBounds(x_px=40.0, y_px=176.0, width_px=120.0, height_px=80.0),
    }
    lanes = (
        SimpleNamespace(id="__sppm_row_mainline", node_ids=("mainline",)),
        SimpleNamespace(id="__sppm_row_rework", node_ids=("rework",)),
    )

    diagnostics = row_gap_diagnostics(
        node_bounds=node_bounds,
        lanes=lanes,
        edge_paths={},
    )

    assert diagnostics == ()


def test_rework_alignment_diagnostics_warns_for_branch_and_return_drift() -> None:
    node_bounds = {
        "decision": LayoutBounds(x_px=40.0, y_px=20.0, width_px=120.0, height_px=80.0),
        "rework": LayoutBounds(x_px=240.0, y_px=140.0, width_px=120.0, height_px=80.0),
        "review": LayoutBounds(x_px=60.0, y_px=20.0, width_px=120.0, height_px=80.0),
    }
    lanes = (
        SimpleNamespace(id="__sppm_row_mainline", node_ids=("decision", "review")),
        SimpleNamespace(id="__sppm_row_rework", node_ids=("rework",)),
    )
    edge_paths = {
        ("decision", "rework"): RoutedEdgePath(
            edge=("decision", "rework"),
            points=(
                LayoutPoint(x_px=100.0, y_px=60.0),
                LayoutPoint(x_px=300.0, y_px=180.0),
            ),
            is_rework=True,
            rework_variant="branch",
        ),
        ("rework", "review"): RoutedEdgePath(
            edge=("rework", "review"),
            points=(
                LayoutPoint(x_px=300.0, y_px=180.0),
                LayoutPoint(x_px=120.0, y_px=60.0),
            ),
            is_rework=True,
            rework_variant="return",
        ),
    }

    diagnostics = rework_alignment_diagnostics(
        node_bounds=node_bounds,
        lanes=lanes,
        edge_paths=edge_paths,
    )

    codes = {diagnostic.code for diagnostic in diagnostics}
    assert "sppm-branch-alignment-delta" in codes
    assert "sppm-return-alignment-delta" in codes


def test_rework_alignment_diagnostics_returns_empty_when_within_tolerance() -> None:
    node_bounds = {
        "decision": LayoutBounds(x_px=40.0, y_px=20.0, width_px=120.0, height_px=80.0),
        "rework": LayoutBounds(x_px=84.0, y_px=140.0, width_px=120.0, height_px=80.0),
        "review": LayoutBounds(x_px=60.0, y_px=20.0, width_px=120.0, height_px=80.0),
    }
    lanes = (
        SimpleNamespace(id="__sppm_row_mainline", node_ids=("decision", "review")),
        SimpleNamespace(id="__sppm_row_rework", node_ids=("rework",)),
    )
    edge_paths = {
        ("decision", "rework"): RoutedEdgePath(
            edge=("decision", "rework"),
            points=(
                LayoutPoint(x_px=100.0, y_px=60.0),
                LayoutPoint(x_px=144.0, y_px=180.0),
            ),
            is_rework=True,
            rework_variant="branch",
        ),
        ("rework", "review"): RoutedEdgePath(
            edge=("rework", "review"),
            points=(
                LayoutPoint(x_px=144.0, y_px=180.0),
                LayoutPoint(x_px=120.0, y_px=60.0),
            ),
            is_rework=True,
            rework_variant="return",
        ),
    }

    diagnostics = rework_alignment_diagnostics(
        node_bounds=node_bounds,
        lanes=lanes,
        edge_paths=edge_paths,
    )

    assert diagnostics == ()
