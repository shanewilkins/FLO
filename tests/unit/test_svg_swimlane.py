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


def test_render_swimlane_svg_artifact_keeps_unlaned_nodes_renderable(monkeypatch):
    def fake_execute_elk_layout(request, *, engine):
        assert [lane.id for lane in request.lanes] == ["sales", "unassigned"]
        assert request.lanes[1].node_ids == ("finish",)
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=280, height_px=180),
            lanes=(
                LayoutLaneFrame(
                    id="sales",
                    label="Sales",
                    bounds=LayoutBounds(x_px=0, y_px=0, width_px=280, height_px=80),
                    node_ids=("start",),
                ),
                LayoutLaneFrame(
                    id="unassigned",
                    label="unassigned",
                    bounds=LayoutBounds(x_px=0, y_px=100, width_px=280, height_px=80),
                    node_ids=("finish",),
                ),
            ),
            node_bounds={
                "start": LayoutBounds(x_px=20, y_px=20, width_px=60, height_px=40),
                "finish": LayoutBounds(x_px=190, y_px=120, width_px=60, height_px=40),
            },
            edge_paths={
                ("start", "finish"): RoutedEdgePath(
                    edge=("start", "finish"),
                    points=(
                        LayoutPoint(x_px=80, y_px=40),
                        LayoutPoint(x_px=140, y_px=40),
                        LayoutPoint(x_px=190, y_px=140),
                    ),
                )
            },
            diagnostics=(),
        )

    monkeypatch.setattr(
        "flo.render._svg_swimlane.execute_elk_layout", fake_execute_elk_layout
    )

    artifact, contract = render_swimlane_svg_artifact(
        {
            "lanes": [{"id": "sales", "name": "Sales"}],
            "nodes": [
                {"id": "start", "kind": "start", "name": "Start", "lane": "sales"},
                {"id": "finish", "kind": "end", "name": "Done"},
            ],
            "edges": [{"source": "start", "target": "finish"}],
        },
        RenderOptions(diagram="swimlane"),
    )

    assert contract is None
    assert 'data-lane-id="unassigned"' in artifact.content
    assert 'data-node-id="finish"' in artifact.content
    assert 'data-edge-source="start"' in artifact.content
    assert 'data-edge-target="finish"' in artifact.content
