from __future__ import annotations

from types import SimpleNamespace

from flo.render._svg_sppm_rows import (
    rework_alignment_diagnostics,
    row_gap_diagnostics,
)
from flo.render.layout_core.models import LayoutBounds, LayoutPoint, RoutedEdgePath


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
