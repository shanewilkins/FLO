import re

import pytest

from flo.render import render_artifact, render_artifact_and_contract, render_dot
from flo.render._svg_sppm import (
    _annotation_bounds_for_placement,
    _edge_callout_placement,
    _label_placement,
    _lane_header_avoid_bounds,
)
from flo.render._svg_sppm_edges import _edge_svg, _normalize_rework_edge_points
from flo.render.layout_core.models import LayoutBounds, LayoutLaneFrame, LayoutPoint


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


def test_render_artifact_direct_svg_sppm_branch_polyline_is_orthogonal():
    ir_like = {
        "nodes": [
            {"id": "decision", "kind": "decision", "name": "Approved?"},
            {"id": "rework", "kind": "task", "name": "Rework"},
        ],
        "edges": [
            {
                "source": "decision",
                "target": "rework",
                "outcome": "no",
                "edge_type": "rework",
                "rework": True,
            }
        ],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    match = re.search(
        r'data-edge-rework-variant="branch"[^>]*>\s*<polyline points="([^"]+)"',
        artifact.content,
    )
    assert match is not None
    points = [
        tuple(float(part) for part in token.split(",", 1))
        for token in match.group(1).split()
    ]
    assert len(points) >= 2
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        assert abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6


def test_render_artifact_direct_svg_sppm_return_polyline_is_orthogonal():
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

    match = re.search(
        r'data-edge-rework-variant="return"[^>]*>\s*<polyline points="([^"]+)"',
        artifact.content,
    )
    assert match is not None
    points = [
        tuple(float(part) for part in token.split(",", 1))
        for token in match.group(1).split()
    ]
    assert len(points) >= 3
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        assert abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6


def test_direct_svg_rework_branch_normalization_is_passthrough() -> None:
    points = (
        LayoutPoint(x_px=260.0, y_px=120.0),
        LayoutPoint(x_px=90.0, y_px=60.0),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=True,
        rework_variant="branch",
    )

    assert normalized == points


def test_direct_svg_rework_return_normalization_is_passthrough() -> None:
    points = (
        LayoutPoint(x_px=1170.37, y_px=-270.0),
        LayoutPoint(x_px=985.71, y_px=-519.89),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=True,
        rework_variant="return",
    )

    assert normalized == points


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


def test_svg_sppm_decision_labels_prefer_near_source_segments():
    points = (
        LayoutPoint(x_px=100.0, y_px=100.0),
        LayoutPoint(x_px=148.0, y_px=100.0),
        LayoutPoint(x_px=148.0, y_px=256.0),
        LayoutPoint(x_px=420.0, y_px=256.0),
    )

    near_source = _label_placement(points, prefer_near_source=True)
    unconstrained = _label_placement(points, prefer_near_source=False)

    assert near_source.x < unconstrained.x
    assert near_source.x == pytest.approx(124.0)
    assert near_source.y == pytest.approx(96.0)


def test_svg_sppm_edge_svg_prefers_elk_label_point_when_available():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("decision", "next"),
            "points": (
                LayoutPoint(x_px=100.0, y_px=100.0),
                LayoutPoint(x_px=220.0, y_px=100.0),
            ),
            "label": "No",
            "label_point": LayoutPoint(x_px=180.0, y_px=82.0),
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    parts, _ = _edge_svg(edge_path)
    svg = "\n".join(parts)

    assert 'x="180.0"' in svg
    assert 'y="83.0"' in svg


def test_svg_sppm_edge_svg_skips_endpoint_clipping_with_explicit_ports():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("task_a", "task_b"),
            "points": (
                LayoutPoint(x_px=120.0, y_px=60.0),
                LayoutPoint(x_px=220.0, y_px=60.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": "EAST",
            "target_port_side": "WEST",
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    parts, _ = _edge_svg(
        edge_path,
        source_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=100.0, height_px=80.0),
        target_bounds=LayoutBounds(
            x_px=240.0, y_px=0.0, width_px=100.0, height_px=80.0
        ),
    )
    svg = "\n".join(parts)

    assert 'points="120.0,60.0 220.0,60.0"' in svg


def test_render_artifact_direct_svg_sppm_task_header_is_top_rounded_only():
    ir_like = {
        "nodes": [
            {
                "id": "task",
                "kind": "task",
                "name": "Assemble",
                "workers": ["Operator"],
            }
        ],
        "edges": [],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    assert 'data-node-header="top-rounded"' in artifact.content


def test_render_artifact_direct_svg_sppm_queue_data_renders_above_title():
    ir_like = {
        "nodes": [
            {
                "id": "queue",
                "kind": "queue",
                "name": "Intake Queue",
                "metadata": {"wait_time": {"value": 12, "unit": "min"}},
            }
        ],
        "edges": [],
    }

    artifact = render_artifact(
        ir_like,
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    queue_group_match = re.search(
        r'data-node-kind="queue">(.*?)</g>',
        artifact.content,
        re.DOTALL,
    )
    assert queue_group_match is not None
    queue_group = queue_group_match.group(1)

    wait_time_match = re.search(r'y="([0-9.]+)"[^>]*>WT: 12 min</text>', queue_group)
    title_match = re.search(r'y="([0-9.]+)"[^>]*>Intake Queue</text>', queue_group)
    assert wait_time_match is not None
    assert title_match is not None
    wait_time_y = float(wait_time_match.group(1))
    title_y = float(title_match.group(1))
    assert wait_time_y < title_y


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
