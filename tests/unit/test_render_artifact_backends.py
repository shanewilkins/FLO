import pytest

from flo.render import render_artifact, render_artifact_and_contract, render_dot
from flo.render._svg_sppm import (
    _annotation_bounds_for_placement,
    _edge_callout_placement,
    _label_placement,
    _lane_header_avoid_bounds,
)
from flo.render.layout_core.models import LayoutBounds, LayoutLaneFrame


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


def test_render_dot_forces_graphviz_even_when_svg_backend_is_requested():
    ir_like = {
        "nodes": [
            {"id": "a", "kind": "task", "name": "A", "location": "one"},
            {"id": "b", "kind": "task", "name": "B", "location": "two"},
        ],
        "edges": [{"source": "a", "target": "b"}],
        "process": {
            "metadata": {
                "locations": [
                    {
                        "id": "one",
                        "name": "One",
                        "metadata": {"spatial": {"x": 0, "y": 0}},
                    },
                    {
                        "id": "two",
                        "name": "Two",
                        "metadata": {"spatial": {"x": 1, "y": 1}},
                    },
                ]
            }
        },
    }

    out = render_dot(ir_like, options={"diagram": "spaghetti", "render_backend": "svg"})

    assert "digraph" in out
    assert "<svg" not in out


def test_render_artifact_can_select_direct_svg_sppm_backend():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {
                "id": "queue",
                "kind": "queue",
                "name": "Intake Queue",
                "metadata": {"wait_time": {"value": 2, "unit": "min"}},
            },
            {
                "id": "task",
                "kind": "task",
                "name": "Handle Intake",
                "workers": ["Coordinator"],
                "metadata": {
                    "value_class": "RNVA",
                    "description": "Capture request details and context.",
                    "cycle_time": {"value": 4, "unit": "min"},
                },
            },
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {"source": "start", "target": "queue"},
            {"source": "queue", "target": "task"},
            {"source": "task", "target": "finish"},
        ],
        "process": {
            "id": "sppm_svg_demo",
            "name": "SPPM SVG Demo",
        },
    }

    artifact, contract = render_artifact_and_contract(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert contract is None
    assert "<svg" in artifact.content
    assert 'data-flo-diagram="sppm"' in artifact.content
    assert 'data-node-kind="queue"' in artifact.content
    assert "SPPM SVG Demo" in artifact.content
    assert "Coordinator" in artifact.content
    assert 'fill="#FFF176"' in artifact.content
    assert 'stroke="#F9A825"' in artifact.content
    assert 'data-node-port-rail="in"' in artifact.content
    assert 'data-node-port-rail="out"' in artifact.content
    assert "WT: 2 min" in artifact.content
    assert "CT: 4 min" in artifact.content


def test_render_dot_and_svg_sppm_share_task_card_structure_cues():
    ir_like = {
        "nodes": [
            {
                "id": "task",
                "kind": "task",
                "name": "Handle Intake",
                "workers": ["Coordinator"],
                "metadata": {
                    "value_class": "RNVA",
                    "description": "Capture request details and context.",
                    "cycle_time": {"value": 4, "unit": "min"},
                },
            },
        ],
        "edges": [],
    }

    artifact = render_artifact(
        ir_like,
        options={"diagram": "sppm", "render_backend": "svg"},
    )
    dot = render_dot(ir_like, options={"diagram": "sppm"})

    assert artifact.kind == "svg"
    assert 'data-node-port-rail="in"' in artifact.content
    assert 'data-node-port-rail="out"' in artifact.content
    assert "Coordinator" in artifact.content
    assert "CT: 4 min" in artifact.content
    assert 'PORT="boundary_in"' in dot
    assert 'PORT="boundary_out"' in dot
    assert 'WIDTH="80"' in dot


def test_render_artifact_direct_svg_sppm_honors_theme_and_subprocess_shapes():
    ir_like = {
        "nodes": [
            {
                "id": "subprocess",
                "kind": "subprocess",
                "name": "Handle Exception",
                "metadata": {"detail_map": "MAP-42"},
            },
            {
                "id": "task",
                "kind": "task",
                "name": "Review",
                "metadata": {"value_class": "RNVA"},
            },
        ],
        "edges": [{"source": "subprocess", "target": "task"}],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
            "sppm_theme": "print",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-node-kind="subprocess"' in artifact.content
    assert "<ellipse" in artifact.content
    assert 'stroke-dasharray="4 4"' in artifact.content
    assert "[Subprocess]" not in artifact.content
    assert "Detail map: MAP-42" in artifact.content
    assert 'fill="#DAE8FC"' in artifact.content
    assert 'stroke="#23527C"' in artifact.content


def test_render_dot_sppm_uses_shared_queue_and_subprocess_content():
    dot = render_dot(
        {
            "nodes": [
                {
                    "id": "queue",
                    "kind": "queue",
                    "name": "A Very Long Queue Name",
                    "metadata": {"wait_time": {"value": 2, "unit": "min"}},
                },
                {
                    "id": "subprocess",
                    "kind": "subprocess",
                    "name": "Handle Exception",
                    "metadata": {"detail_map": "MAP-42"},
                },
            ],
            "edges": [{"source": "queue", "target": "subprocess"}],
        },
        options={"diagram": "sppm"},
    )

    assert "WT: 2 min" in dot
    assert "A Very Long Queue<BR/>Name<BR/>WT: 2 min" in dot
    assert "Handle Exception\\nSubprocess\\nDetail map: MAP-42" in dot
    assert "[Subprocess]" not in dot


def test_render_artifact_direct_svg_sppm_renders_rework_metadata_callout():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework"},
            {"id": "finish", "kind": "end", "name": "Done"},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
                "metadata": {"rate": 0.08, "reason": "Missing approvals"},
            },
            {"source": "rework", "target": "finish"},
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-edge-kind="rework"' in artifact.content
    assert 'data-edge-rework-variant="branch"' in artifact.content
    assert 'stroke-dasharray="8 6"' in artifact.content
    assert "Rate: 8%" in artifact.content
    assert "Reason: Missing approvals" in artifact.content
    assert ">no<" in artifact.content


def test_render_artifact_direct_svg_sppm_styles_rework_return_edges_differently():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework"},
            {"id": "done", "kind": "task", "name": "Done"},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
            },
            {
                "source": "rework",
                "target": "done",
                "edge_type": "rework",
                "rework": True,
            },
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-edge-rework-variant="branch"' in artifact.content
    assert 'data-edge-rework-variant="return"' in artifact.content
    assert 'stroke="#c2410c"' in artifact.content
    assert 'stroke-dasharray="4 6"' in artifact.content


def test_svg_sppm_edge_placement_avoids_source_callout_label_crowding():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(2996.0, 125.0),
        _Point(3006.0, 125.0),
        _Point(3006.0, 183.0),
        _Point(3036.0, 183.0),
    )

    label_placement = _label_placement(points, avoid_near_source=True)
    callout_placement = _edge_callout_placement(
        points,
        near_source=True,
        has_label=True,
    )

    assert label_placement.x > 3010.0
    assert label_placement.y > 170.0
    assert callout_placement.y < 100.0


def test_svg_sppm_return_loop_callout_uses_open_route_segment():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(3250.0, 227.7),
        _Point(3240.0, 227.7),
        _Point(3240.0, 268.0),
        _Point(2224.0, 268.0),
        _Point(2224.0, 156.0),
        _Point(2214.0, 156.0),
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=False,
        has_label=False,
    )

    assert callout_placement.x == pytest.approx(2732.0)
    assert callout_placement.y == pytest.approx(246.0)


def test_svg_sppm_callout_avoids_overlapping_node_bounds_on_open_segment():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(3250.0, 227.7),
        _Point(3240.0, 227.7),
        _Point(3240.0, 268.0),
        _Point(2224.0, 268.0),
        _Point(2224.0, 156.0),
        _Point(2214.0, 156.0),
    )
    overlapping_bounds = (
        LayoutBounds(x_px=2660.0, y_px=228.0, width_px=150.0, height_px=54.0),
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=False,
        has_label=False,
        avoid_bounds=overlapping_bounds,
        box_width=131.9,
        box_height=40.0,
    )

    assert callout_placement.x == pytest.approx(2732.0)
    top = callout_placement.y - 12.0
    bottom = top + 40.0
    assert bottom <= overlapping_bounds[0].y_px or top >= (
        overlapping_bounds[0].y_px + overlapping_bounds[0].height_px
    )


def test_svg_sppm_callout_clamps_to_canvas_when_nudged_upward():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(2996.0, 125.0),
        _Point(3006.0, 125.0),
        _Point(3006.0, 183.0),
        _Point(3036.0, 183.0),
    )
    overlapping_bounds = (
        LayoutBounds(x_px=2920.0, y_px=70.0, width_px=170.0, height_px=70.0),
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=True,
        has_label=True,
        avoid_bounds=overlapping_bounds,
        box_width=138.6,
        box_height=40.0,
        canvas_bounds=LayoutBounds(
            x_px=0.0, y_px=0.0, width_px=4000.0, height_px=400.0
        ),
    )

    assert callout_placement.y >= 12.0


def test_svg_sppm_lane_header_bounds_are_added_to_avoidance_zones():
    lane_bounds = LayoutBounds(x_px=0.0, y_px=0.0, width_px=800.0, height_px=240.0)
    avoid_bounds = _lane_header_avoid_bounds(
        (
            LayoutLaneFrame(
                id="ops",
                label="Operations",
                bounds=lane_bounds,
                node_ids=("a", "b"),
            ),
        )
    )

    assert len(avoid_bounds) == 1
    assert avoid_bounds[0].x_px == 0.0
    assert avoid_bounds[0].y_px == 0.0
    assert avoid_bounds[0].width_px == 800.0
    assert avoid_bounds[0].height_px == 34.0


def test_svg_sppm_callout_avoids_lane_header_zone():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(40.0, 24.0),
        _Point(240.0, 24.0),
    )
    avoid_bounds = _lane_header_avoid_bounds(
        (
            LayoutLaneFrame(
                id="ops",
                label="Operations",
                bounds=LayoutBounds(
                    x_px=0.0, y_px=0.0, width_px=400.0, height_px=220.0
                ),
                node_ids=("a",),
            ),
        )
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=False,
        has_label=False,
        avoid_bounds=avoid_bounds,
        box_width=120.0,
        box_height=40.0,
        canvas_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=400.0, height_px=220.0),
    )

    top = callout_placement.y - 12.0
    bottom = top + 40.0
    assert top >= 34.0 or bottom <= 0.0


def test_svg_sppm_callout_avoids_existing_annotation_bounds():
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    points = (
        _Point(40.0, 24.0),
        _Point(240.0, 24.0),
    )
    existing_annotation = _annotation_bounds_for_placement(
        _label_placement(points),
        box_width=120.0,
        box_height=18.0,
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=False,
        has_label=False,
        avoid_bounds=(existing_annotation,),
        box_width=120.0,
        box_height=40.0,
        canvas_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=400.0, height_px=220.0),
    )

    top = callout_placement.y - 12.0
    bottom = top + 40.0
    assert bottom <= existing_annotation.y_px or top >= (
        existing_annotation.y_px + existing_annotation.height_px
    )


def test_render_artifact_direct_svg_sppm_renders_explicit_continuation_tokens():
    ir_like = {
        "nodes": [
            {"id": "start", "kind": "start", "name": "Start"},
            {"id": "handoff", "kind": "task", "name": "Handoff"},
            {"id": "end", "kind": "end", "name": "End"},
        ],
        "edges": [
            {"source": "start", "target": "handoff"},
            {
                "source": "handoff",
                "target": "end",
                "metadata": {
                    "continuation_to": "P2-OPS",
                    "continuation_from": "P1-H",
                },
            },
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-edge-token="P2-OPS"' in artifact.content
    assert 'data-edge-token="P1-H"' in artifact.content
    assert "P2-OPS" in artifact.content
    assert "P1-H" in artifact.content


def test_render_artifact_svg_spaghetti_people_channel_suppresses_material_routes():
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
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-route-channel="people"' in artifact.content
    assert 'data-route-channel="material"' not in artifact.content
    assert ">P 1x<" in artifact.content
    assert "Pantry" in artifact.content
    assert "Prep Bench" in artifact.content


def test_render_artifact_svg_spaghetti_worker_mode_labels_people_routes_by_worker():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "prep_bench",
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
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
            "spaghetti_people_mode": "worker",
        },
    )

    assert artifact.kind == "svg"
    assert 'data-route-channel="people"' in artifact.content
    assert ">P assistant_baker 1x<" in artifact.content
    assert 'stroke-dasharray="10 4"' not in artifact.content


def test_render_artifact_svg_spaghetti_renders_boundary_polygon_and_label():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ],
                "layout_boundary": {
                    "x": -1.0,
                    "y": -1.0,
                    "width": 6.0,
                    "height": 4.0,
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
            "spaghetti_channel": "material",
        },
    )

    assert artifact.kind == "svg"
    assert 'stroke-dasharray="6 4"' in artifact.content
    assert ">Kitchen Boundary<" in artifact.content
    assert '<polygon points="' in artifact.content


def test_render_artifact_svg_spaghetti_maps_location_kinds_to_svg_shapes():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["tray"],
            },
            {
                "id": "move",
                "kind": "task",
                "name": "Move",
                "location": "corridor",
                "inputs": ["tray"],
                "outputs": ["tray"],
            },
            {
                "id": "bake",
                "kind": "task",
                "name": "Bake",
                "location": "oven",
                "inputs": ["tray"],
            },
        ],
        "edges": [
            {"source": "gather", "target": "move"},
            {"source": "move", "target": "bake"},
        ],
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
                        "id": "corridor",
                        "name": "Corridor",
                        "kind": "transit",
                        "metadata": {"spatial": {"x": 2, "y": 1, "unit": "m"}},
                    },
                    {
                        "id": "oven",
                        "name": "Oven",
                        "kind": "processing",
                        "metadata": {"spatial": {"x": 4, "y": 0, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "material",
        },
    )

    assert (
        '<g data-location-id="pantry" data-location-shape="rect">' in artifact.content
    )
    assert (
        '<g data-location-id="corridor" data-location-shape="diamond">'
        in artifact.content
    )
    assert (
        '<g data-location-id="oven" data-location-shape="ellipse">' in artifact.content
    )
    assert "Pantry" in artifact.content
    assert "Corridor" in artifact.content
    assert "Oven" in artifact.content


def test_render_artifact_svg_spaghetti_material_routes_emit_item_titles_and_labels():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "material",
        },
    )

    assert 'data-route-channel="material"' in artifact.content
    assert ">M 1x<" in artifact.content
    assert "<title>items: flour</title>" in artifact.content
    assert 'stroke="tomato"' in artifact.content


def test_render_artifact_svg_spaghetti_people_routes_emit_titles_and_aggregate_style():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "people",
            "spaghetti_people_mode": "aggregate",
        },
    )

    assert 'data-route-channel="people"' in artifact.content
    assert ">P 1x<" in artifact.content
    assert "<title>workers: assistant_baker</title>" in artifact.content
    assert 'stroke="royalblue"' in artifact.content
    assert 'stroke-dasharray="8 6"' in artifact.content


def test_render_artifact_svg_spaghetti_rejects_missing_spatial_metadata():
    ir_like = {
        "nodes": [
            {
                "id": "gather",
                "kind": "task",
                "name": "Gather",
                "location": "pantry",
                "outputs": ["flour"],
            },
            {
                "id": "mix",
                "kind": "task",
                "name": "Mix",
                "location": "bench",
                "inputs": ["flour"],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                    },
                ]
            }
        },
    }

    with pytest.raises(
        ValueError,
        match=r"Direct SVG spaghetti rendering requires explicit spatial metadata .* Missing: bench",
    ):
        render_artifact(
            ir_like,
            options={
                "diagram": "spaghetti",
                "render_backend": "svg",
                "spaghetti_channel": "material",
            },
        )


def test_render_artifact_svg_spaghetti_aggregates_multi_route_hops_and_counts():
    ir_like = {
        "nodes": [
            {
                "id": "gather_a",
                "kind": "task",
                "name": "Gather A",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "gather_b",
                "kind": "task",
                "name": "Gather B",
                "location": "pantry",
                "outputs": ["flour"],
                "workers": ["lead_baker"],
            },
            {
                "id": "mix_a",
                "kind": "task",
                "name": "Mix A",
                "location": "bench",
                "inputs": ["flour"],
                "outputs": ["dough"],
                "workers": ["assistant_baker"],
            },
            {
                "id": "mix_b",
                "kind": "task",
                "name": "Mix B",
                "location": "bench",
                "inputs": ["flour"],
                "outputs": ["dough"],
                "workers": ["lead_baker"],
            },
            {
                "id": "bake",
                "kind": "task",
                "name": "Bake",
                "location": "oven",
                "inputs": ["dough"],
                "workers": ["assistant_baker", "lead_baker"],
            },
        ],
        "edges": [
            {"source": "gather_a", "target": "mix_a"},
            {"source": "gather_b", "target": "mix_b"},
            {"source": "mix_a", "target": "bake"},
            {"source": "mix_b", "target": "bake"},
        ],
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
                        "id": "bench",
                        "name": "Bench",
                        "kind": "operation",
                        "metadata": {"spatial": {"x": 3, "y": 1, "unit": "m"}},
                    },
                    {
                        "id": "oven",
                        "name": "Oven",
                        "kind": "processing",
                        "metadata": {"spatial": {"x": 6, "y": 0, "unit": "m"}},
                    },
                ]
            }
        },
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "spaghetti",
            "render_backend": "svg",
            "spaghetti_channel": "both",
            "spaghetti_people_mode": "aggregate",
        },
    )

    assert artifact.kind == "svg"
    assert artifact.content.count('data-route-channel="material"') == 2
    assert artifact.content.count('data-route-channel="people"') == 2
    assert artifact.content.count(">M 2x<") == 2
    assert artifact.content.count(">P 2x<") == 2
    assert "<title>items: flour</title>" in artifact.content
    assert "<title>items: dough</title>" in artifact.content
    assert "assistant_baker" in artifact.content
    assert "lead_baker" in artifact.content
    assert 'data-from="pantry" data-to="bench"' in artifact.content
    assert 'data-from="bench" data-to="oven"' in artifact.content
