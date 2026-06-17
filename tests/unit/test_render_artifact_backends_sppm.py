import logging
import re

import pytest

import flo.render._svg_sppm as svg_sppm
from flo.render import render_artifact, render_artifact_and_contract, render_dot
from flo.render._diagnostics import RenderDiagnostic
from flo.render._svg_sppm import (
    _annotation_bounds_for_placement,
    _edge_callout_placement,
    _label_placement,
    _lane_header_avoid_bounds,
)
from flo.render._svg_sppm_edges import _edge_svg, _normalize_rework_edge_points
from flo.render._svg_sppm_rows import (
    _display_canvas_bounds,
    rework_alignment_diagnostics,
    row_gap_diagnostics,
)
from flo.render.layout_core.models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.services.errors import RenderError
from flo.services.logging import configure_logging


def test_render_artifact_can_select_direct_svg_sppm_backend():
    artifact, contract = render_artifact_and_contract(
        _direct_svg_sppm_demo_ir(),
        options={
            "diagram": "sppm",
            "render_backend": "svg",
        },
    )

    _assert_direct_svg_sppm_demo_artifact(artifact, contract)


def _direct_svg_sppm_demo_ir() -> dict[str, object]:
    return {
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


def _assert_direct_svg_sppm_demo_artifact(artifact, contract) -> None:
    _assert_direct_svg_sppm_demo_metadata(artifact, contract)
    _assert_direct_svg_sppm_demo_content(artifact)


def _assert_direct_svg_sppm_demo_metadata(artifact, contract) -> None:
    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert contract is None
    assert "<svg" in artifact.content
    assert 'data-flo-diagram="sppm"' in artifact.content
    assert 'data-node-kind="queue"' in artifact.content


def _assert_direct_svg_sppm_demo_content(artifact) -> None:
    assert "SPPM SVG Demo" in artifact.content
    assert "Coordinator" in artifact.content
    assert 'fill="#FFF176"' in artifact.content
    assert 'stroke="#F9A825"' in artifact.content
    assert 'data-node-port-rail="in"' not in artifact.content
    assert 'data-node-port-rail="out"' not in artifact.content
    assert 'data-node-queue-body="true"' in artifact.content
    assert 'data-node-queue-label-band="true"' in artifact.content
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
    assert 'data-node-port-rail="in"' not in artifact.content
    assert 'data-node-port-rail="out"' not in artifact.content
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
    assert 'stroke-dasharray="2 6"' in artifact.content
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
    assert artifact.content.count('stroke-dasharray="2 6"') >= 2


def test_render_artifact_sppm_svg_logs_and_serializes_render_diagnostics(
    monkeypatch, capsys
):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=260, height_px=140),
            node_bounds={
                "task": LayoutBounds(x_px=60, y_px=40, width_px=140, height_px=60),
            },
            edge_paths={},
            diagnostics=(
                RenderDiagnostic(
                    code="elk-lane-frame-missing",
                    severity="warning",
                    message="ELK response did not produce geometry for expected lane 'front'.",
                    metadata={"lane_id": "front"},
                ),
            ),
        )

    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    try:
        root.handlers.clear()
        configure_logging(level=logging.INFO)
        monkeypatch.setattr(svg_sppm, "execute_elk_layout", fake_execute_elk_layout)

        artifact = render_artifact(
            {
                "lanes": [{"id": "front", "name": "Front"}],
                "nodes": [
                    {
                        "id": "task",
                        "kind": "task",
                        "name": "Handle Intake",
                        "lane": "front",
                    }
                ],
                "edges": [],
            },
            options={"diagram": "sppm", "render_backend": "svg"},
        )

        assert artifact.metadata["render_diagnostics"] == [
            {
                "code": "elk-lane-frame-missing",
                "severity": "warning",
                "message": "ELK response did not produce geometry for expected lane 'front'.",
                "lane_id": "front",
            }
        ]
        assert artifact.metadata["render_diagnostics_report"] == {
            "diagram": "sppm",
            "backend": "svg",
            "artifact_kind": "svg",
            "strict": False,
            "warning_count": 1,
            "error_count": 0,
            "diagnostic_count": 1,
            "code_counts": {"elk-lane-frame-missing": 1},
            "category_counts": {"missing_geometry": 1},
            "partial_output": True,
            "summary": "1 warning(s) while rendering sppm via svg",
            "diagnostics": [
                {
                    "code": "elk-lane-frame-missing",
                    "severity": "warning",
                    "message": "ELK response did not produce geometry for expected lane 'front'.",
                    "lane_id": "front",
                }
            ],
        }
        captured = capsys.readouterr()
        assert "render_diagnostics_summary" in captured.err
        assert "render_diagnostic" in captured.err
        assert "elk-lane-frame-missing" in captured.err
        assert "expected lane 'front'" in captured.err
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)


def test_row_gap_diagnostics_flags_tight_mainline_to_rework_spacing():
    diagnostics = row_gap_diagnostics(
        node_bounds={
            "qa": LayoutBounds(x_px=180, y_px=20, width_px=120, height_px=80),
            "rework_quality_wait_queue": LayoutBounds(
                x_px=200, y_px=70, width_px=120, height_px=120
            ),
            "rework_quality": LayoutBounds(
                x_px=120, y_px=90, width_px=160, height_px=80
            ),
        },
        lanes=(),
        edge_paths={
            ("qa", "rework_quality_wait_queue"): RoutedEdgePath(
                edge=("qa", "rework_quality_wait_queue"),
                points=(
                    LayoutPoint(x_px=240, y_px=100),
                    LayoutPoint(x_px=240, y_px=120),
                ),
                is_rework=True,
                rework_variant="branch",
            ),
            ("rework_quality_wait_queue", "rework_quality"): RoutedEdgePath(
                edge=("rework_quality_wait_queue", "rework_quality"),
                points=(
                    LayoutPoint(x_px=200, y_px=140),
                    LayoutPoint(x_px=160, y_px=140),
                ),
            ),
            ("rework_quality", "qa"): RoutedEdgePath(
                edge=("rework_quality", "qa"),
                points=(
                    LayoutPoint(x_px=120, y_px=130),
                    LayoutPoint(x_px=180, y_px=130),
                ),
                is_rework=True,
                rework_variant="return",
            ),
        },
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "sppm-row-gap-tight"
    assert diagnostics[0].severity == "warning"


def test_direct_svg_rework_return_normalization_straightens_near_vertical_paths() -> (
    None
):
    points = (
        LayoutPoint(x_px=1261.5, y_px=144.0),
        LayoutPoint(x_px=1252.1, y_px=144.0),
        LayoutPoint(x_px=1252.1, y_px=156.9),
        LayoutPoint(x_px=1270.9, y_px=156.9),
        LayoutPoint(x_px=1270.9, y_px=245.1),
        LayoutPoint(x_px=1261.5, y_px=245.1),
        LayoutPoint(x_px=1261.5, y_px=258.0),
    )

    normalized = _normalize_rework_edge_points(
        points,
        is_rework=True,
        rework_variant="branch",
    )

    assert normalized == (
        LayoutPoint(x_px=1261.5, y_px=144.0),
        LayoutPoint(x_px=1261.5, y_px=258.0),
    )


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


def test_svg_sppm_edge_svg_rework_branch_label_stays_on_line_not_label_point():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("information_complete", "rework_intake_wait_queue"),
            "points": (
                LayoutPoint(x_px=1261.5, y_px=144.0),
                LayoutPoint(x_px=1252.1, y_px=144.0),
                LayoutPoint(x_px=1252.1, y_px=156.9),
                LayoutPoint(x_px=1270.9, y_px=156.9),
                LayoutPoint(x_px=1270.9, y_px=245.1),
                LayoutPoint(x_px=1261.5, y_px=245.1),
                LayoutPoint(x_px=1261.5, y_px=258.0),
            ),
            "label": "no",
            "label_point": LayoutPoint(x_px=1412.0, y_px=158.0),
            "is_rework": True,
            "rework_variant": "branch",
            "callout_lines": (),
            "callout_near_source": True,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    parts, _ = _edge_svg(edge_path)
    svg = "\n".join(parts)

    assert 'points="1261.5,144.0 1261.5,258.0"' in svg
    assert 'x="1412.0"' not in svg
    assert 'x="1261.5"' in svg


def test_svg_sppm_edge_svg_clips_endpoints_even_with_explicit_ports():
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

    assert 'points="100.0,40.0 240.0,40.0"' in svg


def test_svg_sppm_rework_callout_is_offset_beside_vertical_line():
    points = (
        LayoutPoint(x_px=1261.5, y_px=144.0),
        LayoutPoint(x_px=1261.5, y_px=258.0),
    )

    callout_placement = _edge_callout_placement(
        points,
        near_source=True,
        has_label=True,
        rework_edge=True,
        box_width=172.1,
        box_height=40.0,
    )

    assert callout_placement.x > (1261.5 + (172.1 / 2.0))


def test_display_canvas_bounds_tightens_to_rendered_content_extents():
    base_canvas = LayoutBounds(x_px=0.0, y_px=0.0, width_px=5200.0, height_px=900.0)
    node_bounds = {
        "a": LayoutBounds(x_px=120.0, y_px=20.0, width_px=200.0, height_px=80.0),
        "b": LayoutBounds(x_px=900.0, y_px=40.0, width_px=180.0, height_px=90.0),
    }
    edge_paths = {
        ("a", "b"): RoutedEdgePath(
            edge=("a", "b"),
            points=(
                LayoutPoint(x_px=320.0, y_px=60.0),
                LayoutPoint(x_px=960.0, y_px=60.0),
            ),
        ),
    }

    bounds = _display_canvas_bounds(
        base_canvas=base_canvas,
        node_bounds=node_bounds,
        edge_paths=edge_paths,
    )

    assert bounds.width_px == pytest.approx(1080.0)
    assert bounds.height_px == pytest.approx(130.0)


def test_display_canvas_bounds_falls_back_to_base_for_empty_content():
    base_canvas = LayoutBounds(x_px=0.0, y_px=0.0, width_px=640.0, height_px=480.0)

    bounds = _display_canvas_bounds(
        base_canvas=base_canvas,
        node_bounds={},
        edge_paths={},
    )

    assert bounds == base_canvas


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


def test_svg_sppm_edge_svg_clips_queue_endpoint_to_triangle_boundary():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("queue", "task"),
            "points": (
                LayoutPoint(x_px=50.0, y_px=50.0),
                LayoutPoint(x_px=220.0, y_px=50.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
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
        source_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=100.0, height_px=100.0),
        target_bounds=LayoutBounds(
            x_px=220.0, y_px=20.0, width_px=120.0, height_px=80.0
        ),
        source_kind="queue",
        target_kind="task",
    )
    svg = "\n".join(parts)

    # Queue edge should clip at the triangle right boundary, not its center,
    # while preserving a straight horizontal segment.
    points_match = re.search(r'points="([0-9.]+),([0-9.]+) 220.0,60.0"', svg)
    assert points_match is not None
    source_x = float(points_match.group(1))
    source_y = float(points_match.group(2))
    assert source_x == 75.0
    assert source_y == 50.0


def test_render_artifact_direct_svg_sppm_includes_postprocess_diagnostics_in_report(
    monkeypatch,
):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=260, height_px=140),
            node_bounds={
                "task": LayoutBounds(x_px=60, y_px=40, width_px=140, height_px=60),
            },
            edge_paths={},
        )

    def fake_row_gap_diagnostics(**_kwargs):
        return (
            RenderDiagnostic(
                code="sppm-row-gap-tight",
                severity="warning",
                message="Mainline-to-rework row separation is below the minimum spacing target.",
                metadata={"measured_gap_px": 12.0, "min_gap_px": 56.0},
            ),
        )

    monkeypatch.setattr(svg_sppm, "execute_elk_layout", fake_execute_elk_layout)
    monkeypatch.setattr(svg_sppm, "row_gap_diagnostics", fake_row_gap_diagnostics)

    artifact = render_artifact(
        {
            "nodes": [
                {"id": "task", "kind": "task", "name": "Handle Intake"},
            ],
            "edges": [],
        },
        options={"diagram": "sppm", "render_backend": "svg"},
    )

    report = artifact.metadata["render_diagnostics_report"]
    assert report["code_counts"]["sppm-row-gap-tight"] == 1
    assert report["category_counts"]["uncategorized"] >= 1


def test_render_artifact_direct_svg_sppm_reports_overlap_fallback_diagnostic(
    monkeypatch,
):
    class _Point:
        def __init__(self, x_px: float, y_px: float) -> None:
            self.x_px = x_px
            self.y_px = y_px

    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("a", "b"),
            "points": (
                _Point(40.0, 24.0),
                _Point(240.0, 24.0),
            ),
            "label": None,
            "label_point": None,
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": ("Needs review",),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    diagnostics: list[RenderDiagnostic] = []
    _edge_svg(
        edge_path,
        avoid_bounds=(
            LayoutBounds(x_px=0.0, y_px=0.0, width_px=320.0, height_px=160.0),
        ),
        canvas_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=320.0, height_px=160.0),
        diagnostics=diagnostics,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "sppm-annotation-overlap-fallback"
    assert diagnostics[0].severity == "warning"
    assert diagnostics[0].metadata["annotation_kind"] == "edge_callout"
    assert diagnostics[0].metadata["edge"] == "a->b"


def test_svg_sppm_edge_svg_reports_large_attachment_correction_diagnostic():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("task_a", "task_b"),
            "points": (
                LayoutPoint(x_px=150.0, y_px=40.0),
                LayoutPoint(x_px=220.0, y_px=40.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    diagnostics: list[RenderDiagnostic] = []
    _edge_svg(
        edge_path,
        source_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=100.0, height_px=80.0),
        target_bounds=LayoutBounds(
            x_px=240.0, y_px=0.0, width_px=100.0, height_px=80.0
        ),
        diagnostics=diagnostics,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "sppm-attachment-miss-distance"
    assert diagnostics[0].severity == "warning"
    assert diagnostics[0].metadata["edge"] == "task_a->task_b"
    assert diagnostics[0].metadata["endpoint_role"] == "source"


def test_svg_sppm_edge_svg_allows_expected_queue_triangle_attachment_correction():
    edge_path = type(
        "_EdgePath",
        (),
        {
            "edge": ("queue_a", "task_b"),
            "points": (
                LayoutPoint(x_px=200.0, y_px=80.0),
                LayoutPoint(x_px=280.0, y_px=80.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    diagnostics: list[RenderDiagnostic] = []
    _edge_svg(
        edge_path,
        source_bounds=LayoutBounds(x_px=0.0, y_px=0.0, width_px=200.0, height_px=160.0),
        source_kind="queue",
        target_bounds=LayoutBounds(
            x_px=280.0, y_px=0.0, width_px=120.0, height_px=160.0
        ),
        target_kind="task",
        diagnostics=diagnostics,
    )

    assert diagnostics == []


def test_svg_sppm_rework_edges_use_consistent_dotted_dash_pattern():
    branch_edge = type(
        "_EdgePath",
        (),
        {
            "edge": ("a", "b"),
            "points": (
                LayoutPoint(x_px=0.0, y_px=0.0),
                LayoutPoint(x_px=100.0, y_px=0.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
            "is_rework": True,
            "rework_variant": "branch",
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()
    return_edge = type(
        "_EdgePath",
        (),
        {
            "edge": ("b", "c"),
            "points": (
                LayoutPoint(x_px=100.0, y_px=0.0),
                LayoutPoint(x_px=200.0, y_px=0.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
            "is_rework": True,
            "rework_variant": "return",
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    branch_parts, _ = _edge_svg(branch_edge)
    return_parts, _ = _edge_svg(return_edge)

    branch_svg = "\n".join(branch_parts)
    return_svg = "\n".join(return_parts)
    assert 'stroke-dasharray="2 6"' in branch_svg
    assert 'stroke-dasharray="2 6"' in return_svg


def test_svg_sppm_non_branch_rework_row_edge_can_render_with_rework_style():
    row_edge = type(
        "_EdgePath",
        (),
        {
            "edge": ("rework_queue", "rework_task"),
            "points": (
                LayoutPoint(x_px=0.0, y_px=0.0),
                LayoutPoint(x_px=100.0, y_px=0.0),
            ),
            "label": None,
            "label_point": None,
            "source_port_side": None,
            "target_port_side": None,
            "is_rework": False,
            "rework_variant": None,
            "callout_lines": (),
            "callout_near_source": False,
            "outgoing_token": None,
            "incoming_token": None,
        },
    )()

    parts, _ = _edge_svg(row_edge, render_as_rework_style=True)

    assert 'stroke-dasharray="2 6"' in "\n".join(parts)


def test_rework_alignment_diagnostics_flag_branch_and_return_drift():
    diagnostics = rework_alignment_diagnostics(
        node_bounds={
            "qa": LayoutBounds(x_px=100.0, y_px=20.0, width_px=120.0, height_px=80.0),
            "rework_queue": LayoutBounds(
                x_px=260.0, y_px=160.0, width_px=120.0, height_px=80.0
            ),
            "rework_task": LayoutBounds(
                x_px=280.0, y_px=260.0, width_px=140.0, height_px=80.0
            ),
            "done": LayoutBounds(x_px=120.0, y_px=20.0, width_px=120.0, height_px=80.0),
        },
        lanes=(),
        edge_paths={
            ("qa", "rework_queue"): RoutedEdgePath(
                edge=("qa", "rework_queue"),
                points=(
                    LayoutPoint(x_px=160.0, y_px=100.0),
                    LayoutPoint(x_px=320.0, y_px=160.0),
                ),
                is_rework=True,
                rework_variant="branch",
            ),
            ("rework_queue", "rework_task"): RoutedEdgePath(
                edge=("rework_queue", "rework_task"),
                points=(
                    LayoutPoint(x_px=320.0, y_px=200.0),
                    LayoutPoint(x_px=350.0, y_px=260.0),
                ),
            ),
            ("rework_task", "done"): RoutedEdgePath(
                edge=("rework_task", "done"),
                points=(
                    LayoutPoint(x_px=350.0, y_px=300.0),
                    LayoutPoint(x_px=180.0, y_px=100.0),
                ),
                is_rework=True,
                rework_variant="return",
            ),
        },
    )

    assert len(diagnostics) == 2
    assert diagnostics[0].code == "sppm-branch-alignment-delta"
    assert diagnostics[1].code == "sppm-return-alignment-delta"


def test_render_artifact_direct_svg_sppm_raises_for_strict_postprocess_diagnostic(
    monkeypatch,
):
    def fake_execute_elk_layout(_request, *, engine):
        return LayoutResult(
            orientation="lr",
            canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=260, height_px=140),
            node_bounds={
                "task": LayoutBounds(x_px=60, y_px=40, width_px=140, height_px=60),
            },
            edge_paths={},
        )

    def fake_row_gap_diagnostics(**_kwargs):
        return (
            RenderDiagnostic(
                code="sppm-attachment-miss-distance",
                severity="warning",
                message="SPPM endpoint clipping required a large attachment correction from the ELK endpoint.",
                metadata={"edge": "task->task"},
            ),
        )

    monkeypatch.setattr(svg_sppm, "execute_elk_layout", fake_execute_elk_layout)
    monkeypatch.setattr(svg_sppm, "row_gap_diagnostics", fake_row_gap_diagnostics)
    monkeypatch.setattr(svg_sppm, "rework_alignment_diagnostics", lambda **_kwargs: ())

    with pytest.raises(
        RenderError, match="Strict SPPM post-process diagnostics failed"
    ):
        render_artifact(
            {
                "nodes": [
                    {"id": "task", "kind": "task", "name": "Handle Intake"},
                ],
                "edges": [],
            },
            options={
                "diagram": "sppm",
                "render_backend": "svg",
                "layout_fit": "fit-strict",
            },
        )
