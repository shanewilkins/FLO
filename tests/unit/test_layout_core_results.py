"""Unit tests for backend-neutral final layout geometry contracts."""

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
