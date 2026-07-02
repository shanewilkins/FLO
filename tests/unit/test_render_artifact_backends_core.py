import logging

import flo.render._svg_flowchart as svg_flowchart
from flo.render import render_artifact
from flo.render._diagnostics import RenderDiagnostic
from flo.render.layout_core.models import (
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.services.logging import configure_logging


def test_render_artifact_can_select_direct_svg_flowchart_backend():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "review", "kind": "decision", "name": "Approved?"},
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "review"},
            {"source": "review", "target": "finish", "outcome": "yes"},
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "flowchart",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert "<svg" in artifact.content
    assert 'data-flo-diagram="flowchart"' in artifact.content
    assert 'data-node-id="start"' in artifact.content
    assert 'data-node-kind="decision"' in artifact.content
    assert 'data-edge-source="review"' in artifact.content
    assert ">yes<" in artifact.content


def test_render_artifact_can_select_direct_svg_spaghetti_backend():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
                "inputs": ["flour"],
                "workers": ["assistant_baker"],
            },
        ],
        "edges": [{"source": "gather", "target": "mix"}],
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "pantry",
                        "name": "Pantry",
                        "kind": "storage",
                        "metadata": {"spatial": {"x": 0, "y": 0, "unit": "m"}},
                    },
                    {
                        "id": "prep_bench",
                        "name": "Prep Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 4, "unit": "m"}},
                    },
                ],
                "layout_boundary": {
                    "x": -1.0,
                    "y": -1.0,
                    "width": 6.0,
                    "height": 7.0,
                    "label": "Kitchen Boundary",
                },
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "detail": "verbose",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert "<svg" in artifact.content
    assert 'data-route-channel="material"' in artifact.content
    assert 'data-route-channel="people"' in artifact.content
    assert "Kitchen Boundary" in artifact.content
    assert "Pantry" in artifact.content
    assert "Prep Bench" in artifact.content


def test_render_artifact_flowchart_svg_logs_and_serializes_render_diagnostics(
    monkeypatch, capsys
):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=240, height_px=120),
            node_bounds={
                "start": LayoutBounds(x_px=20, y_px=34, width_px=100, height_px=52),
                "finish": LayoutBounds(x_px=140, y_px=34, width_px=100, height_px=52),
            },
            edge_paths={
                ("start", "finish"): RoutedEdgePath(
                    edge=("start", "finish"),
                    points=(
                        LayoutPoint(x_px=120, y_px=60),
                        LayoutPoint(x_px=140, y_px=60),
                    ),
                )
            },
            diagnostics=(
                RenderDiagnostic(
                    code="elk-edge-missing",
                    severity="warning",
                    message="ELK response did not normalize requested edge 'start->finish'.",
                    metadata={"source_id": "start", "target_id": "finish"},
                ),
            ),
        )

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        root.handlers.clear()
        configure_logging(level=logging.INFO)
        monkeypatch.setattr(
            svg_flowchart, "execute_elk_layout", fake_execute_elk_layout
        )

        artifact = render_artifact(
            {
                "nodes": [
                    {"id": "start", "kind": "start", "name": "Start"},
                    {"id": "finish", "kind": "end", "name": "Finish"},
                ],
                "edges": [{"source": "start", "target": "finish"}],
            },
            options={"diagram": "flowchart", "render_backend": "svg"},
        )

        assert artifact.metadata["render_diagnostics"] == [
            {
                "code": "elk-edge-missing",
                "severity": "warning",
                "message": "ELK response did not normalize requested edge 'start->finish'.",
                "source_id": "start",
                "target_id": "finish",
            }
        ]
        assert artifact.metadata["render_diagnostics_report"] == {
            "diagram": "flowchart",
            "backend": "svg",
            "artifact_kind": "svg",
            "strict": False,
            "warning_count": 1,
            "error_count": 0,
            "diagnostic_count": 1,
            "code_counts": {"elk-edge-missing": 1},
            "category_counts": {"missing_geometry": 1},
            "partial_output": True,
            "summary": "1 warning(s) while rendering flowchart via svg",
            "diagnostics": [
                {
                    "code": "elk-edge-missing",
                    "severity": "warning",
                    "message": "ELK response did not normalize requested edge 'start->finish'.",
                    "source_id": "start",
                    "target_id": "finish",
                }
            ],
        }
        captured = capsys.readouterr()
        assert "render_diagnostics_summary" in captured.err
        assert "render_diagnostic" in captured.err
        assert "elk-edge-missing" in captured.err
        assert "start->finish" in captured.err
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)
