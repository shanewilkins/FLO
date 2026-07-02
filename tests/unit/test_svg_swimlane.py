from flo.render._svg_swimlane import render_swimlane_svg_artifact
from flo.render.layout_core.models import LayoutBounds, LayoutLaneFrame, LayoutPoint
from flo.render.layout_core.models import LayoutResult, RoutedEdgePath
from flo.render.options import RenderOptions


def test_render_swimlane_svg_artifact_renders_lanes_nodes_and_edges(monkeypatch):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=360, height_px=180),
            lanes=(
                LayoutLaneFrame(
                    id="sales",
                    label="Sales",
                    bounds=LayoutBounds(x_px=0, y_px=0, width_px=360, height_px=80),
                    node_ids=("start", "decision"),
                ),
                LayoutLaneFrame(
                    id="ops",
                    label="Ops",
                    bounds=LayoutBounds(x_px=0, y_px=100, width_px=360, height_px=80),
                    node_ids=("task", "end"),
                ),
            ),
            node_bounds={
                "start": LayoutBounds(x_px=20, y_px=20, width_px=60, height_px=40),
                "decision": LayoutBounds(x_px=120, y_px=12, width_px=70, height_px=56),
                "task": LayoutBounds(x_px=210, y_px=116, width_px=80, height_px=48),
                "end": LayoutBounds(x_px=310, y_px=120, width_px=60, height_px=40),
            },
            edge_paths={
                ("decision", "task"): RoutedEdgePath(
                    edge=("decision", "task"),
                    points=(
                        LayoutPoint(x_px=190, y_px=40),
                        LayoutPoint(x_px=220, y_px=40),
                        LayoutPoint(x_px=220, y_px=116),
                    ),
                    label="yes",
                )
            },
            diagnostics=(),
        )

    monkeypatch.setattr(
        "flo.render._svg_swimlane.execute_elk_layout", fake_execute_elk_layout
    )

    process = {
        "lanes": [
            {"id": "sales", "name": "Sales"},
            {"id": "ops", "name": "Ops"},
        ],
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
            {
                "id": "decision",
                "kind": "decision",
                "name": "Approved?",
                "lane": "sales",
            },
            {"id": "task", "kind": "task", "name": "Do Work", "lane": "ops"},
            {"id": "end", "kind": "end", "name": "Done", "lane": "ops"},
        ],
        "edges": [{"source": "decision", "target": "task", "outcome": "yes"}],
    }

    artifact, contract = render_swimlane_svg_artifact(
        process, RenderOptions(diagram="swimlane")
    )

    assert contract is None
    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert 'data-flo-diagram="swimlane"' in artifact.content
    assert 'data-lane-id="sales"' in artifact.content
    assert 'data-lane-id="ops"' in artifact.content
    assert 'data-node-kind="start"' in artifact.content
    assert 'data-node-kind="decision"' in artifact.content
    assert 'data-node-kind="task"' in artifact.content
    assert 'data-node-kind="end"' in artifact.content
    assert 'data-edge-source="decision"' in artifact.content
    assert 'data-edge-target="task"' in artifact.content
    assert ">yes<" in artifact.content
