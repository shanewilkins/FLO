"""Unit tests for backend-neutral final layout geometry contracts."""

from flo.render._diagnostics import RenderDiagnostic
from flo.render.layout_core import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
    serialize_layout_result,
)


def test_layout_result_exposes_lookup_helpers():
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=420, height_px=180),
        node_bounds={
            "start": LayoutBounds(x_px=20, y_px=24, width_px=120, height_px=52),
            "review": LayoutBounds(x_px=220, y_px=96, width_px=140, height_px=52),
        },
        edge_paths={
            ("start", "review"): RoutedEdgePath(
                edge=("start", "review"),
                label="approved",
                points=(
                    LayoutPoint(x_px=140, y_px=50),
                    LayoutPoint(x_px=180, y_px=50),
                    LayoutPoint(x_px=180, y_px=122),
                    LayoutPoint(x_px=220, y_px=122),
                ),
            )
        },
        lanes=(
            LayoutLaneFrame(
                id="ops",
                label="Operations",
                bounds=LayoutBounds(x_px=0, y_px=80, width_px=420, height_px=100),
                node_ids=("review",),
            ),
        ),
    )

    assert result.bounds_for("start") == LayoutBounds(
        x_px=20, y_px=24, width_px=120, height_px=52
    )
    assert result.bounds_for("missing") is None
    assert result.path_for("start", "review") == RoutedEdgePath(
        edge=("start", "review"),
        label="approved",
        points=(
            LayoutPoint(x_px=140, y_px=50),
            LayoutPoint(x_px=180, y_px=50),
            LayoutPoint(x_px=180, y_px=122),
            LayoutPoint(x_px=220, y_px=122),
        ),
    )
    assert result.path_for("review", "finish") is None


def test_layout_result_snapshot_is_stable():
    result = LayoutResult(
        orientation="tb",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=300, height_px=360),
        node_bounds={
            "finish": LayoutBounds(x_px=96, y_px=280, width_px=108, height_px=44),
            "start": LayoutBounds(x_px=96, y_px=24, width_px=108, height_px=44),
        },
        edge_paths={
            ("start", "finish"): RoutedEdgePath(
                edge=("start", "finish"),
                points=(
                    LayoutPoint(x_px=150, y_px=68),
                    LayoutPoint(x_px=150, y_px=172),
                    LayoutPoint(x_px=150, y_px=280),
                ),
            )
        },
        lanes=(
            LayoutLaneFrame(
                id="requester",
                label="Requester",
                bounds=LayoutBounds(x_px=24, y_px=0, width_px=252, height_px=180),
                node_ids=("start",),
            ),
            LayoutLaneFrame(
                id="manager",
                label="Manager",
                bounds=LayoutBounds(x_px=24, y_px=180, width_px=252, height_px=180),
                node_ids=("finish",),
            ),
        ),
    )

    expected = "\n".join(
        [
            "canvas x=0 y=0 w=300 h=360",
            "orientation tb",
            "lane requester label=Requester x=24 y=0 w=252 h=180 nodes=start",
            "lane manager label=Manager x=24 y=180 w=252 h=180 nodes=finish",
            "node finish x=96 y=280 w=108 h=44",
            "node start x=96 y=24 w=108 h=44",
            "edge start->finish points=(150,68) -> (150,172) -> (150,280)",
        ]
    )

    assert serialize_layout_result(result) == expected


def test_layout_result_can_materialize_render_diagnostics_report():
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=240, height_px=120),
        node_bounds={
            "start": LayoutBounds(x_px=20, y_px=34, width_px=100, height_px=52),
            "finish": LayoutBounds(x_px=140, y_px=34, width_px=100, height_px=52),
        },
        edge_paths={},
        diagnostics=(
            RenderDiagnostic(
                code="elk-edge-missing",
                severity="warning",
                message="ELK response did not normalize requested edge 'start->finish'.",
                metadata={"source_id": "start", "target_id": "finish"},
            ),
        ),
    )

    report = result.diagnostics_report(
        diagram="flowchart",
        backend="elk",
        artifact_kind="layout_result",
    )

    assert report.diagram == "flowchart"
    assert report.backend == "elk"
    assert report.artifact_kind == "layout_result"
    assert report.warning_count == 1
    assert report.error_count == 0
    assert report.code_counts == {"elk-edge-missing": 1}
    assert report.category_counts == {"missing_geometry": 1}
    assert report.partial_output is True
    assert report.summary == "1 warning(s) while rendering flowchart via elk"


def test_layout_result_diagnostics_report_does_not_mark_advisory_output_as_partial():
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=240, height_px=120),
        node_bounds={},
        edge_paths={},
        diagnostics=(
            RenderDiagnostic(
                code="custom-advisory-warning",
                severity="warning",
                message="Renderer used an advisory-only fallback note.",
            ),
        ),
    )

    report = result.diagnostics_report(
        diagram="flowchart",
        backend="elk",
        artifact_kind="layout_result",
    )

    assert report.category_counts == {"uncategorized": 1}
    assert report.partial_output is False
