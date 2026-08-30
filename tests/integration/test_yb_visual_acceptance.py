from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pytest

from flo.source import parse_adapter
from flo.source import compile_adapter
from flo.render import RenderOptions, render_artifact_and_contract
from flo.render.layout_core import (
    LayoutBounds,
    execute_elk_layout,
    run_elkjs_layout,
)
from flo.render.sppm.layout import build_sppm_elk_layout_request
from flo.render.swimlane.layout import build_swimlane_elk_layout_request


REPO_ROOT = Path(__file__).resolve().parents[2]
YB_ROOT = REPO_ROOT / "examples" / "yb"


def _compile(name: str):
    path = YB_ROOT / name
    adapter = parse_adapter(path.read_text(encoding="utf-8"), source_path=str(path))
    return compile_adapter(adapter)


def _overlaps(left: LayoutBounds, right: LayoutBounds) -> bool:
    return not (
        left.x_px + left.width_px <= right.x_px
        or right.x_px + right.width_px <= left.x_px
        or left.y_px + left.height_px <= right.y_px
        or right.y_px + right.height_px <= left.y_px
    )


@pytest.mark.parametrize(
    ("source_name", "diagram"),
    [
        ("linear.flo", "sppm"),
        ("simple_decision.flo", "sppm"),
        ("three_lane_handoff.flo", "swimlane"),
        ("rework_loop.flo", "sppm"),
    ],
)
def test_yb_acceptance_models_render_complete_nonoverlapping_svg(
    source_name: str, diagram: str
):
    ir = _compile(source_name)
    options = RenderOptions(diagram=diagram)
    builder = (
        build_sppm_elk_layout_request
        if diagram == "sppm"
        else build_swimlane_elk_layout_request
    )
    request = builder(ir, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    artifact, _contract = render_artifact_and_contract(ir, options=options)

    assert artifact.kind == "svg"
    assert f'data-flo-diagram="{diagram}"' in artifact.content
    assert set(result.node_bounds) == {node.id for node in request.nodes}
    assert set(result.edge_paths) == {
        (edge.source_id, edge.target_id) for edge in request.edges
    }
    assert not result.diagnostics
    for left, right in combinations(result.node_bounds.values(), 2):
        assert not _overlaps(left, right)

    start = next(node for node in request.nodes if node.kind == "start")
    finish = next(node for node in request.nodes if node.kind == "end")
    start_bounds = result.node_bounds[start.id]
    finish_bounds = result.node_bounds[finish.id]
    assert start_bounds.x_px < finish_bounds.x_px


def test_three_lane_handoff_preserves_responsibility_order_and_labels():
    ir = _compile("three_lane_handoff.flo")
    options = RenderOptions(diagram="swimlane")
    request = build_swimlane_elk_layout_request(ir, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    artifact, _contract = render_artifact_and_contract(ir, options=options)

    lane_ids = [lane.id for lane in result.lanes]
    assert lane_ids == [
        "unassigned_start",
        "requester",
        "manager",
        "operations",
        "unassigned_end",
    ]
    assert [lane.bounds.x_px for lane in result.lanes] == sorted(
        lane.bounds.x_px for lane in result.lanes
    )
    for label in ("Process start", "Requester", "Manager", "Operations", "Process end"):
        assert f">{label}</text>" in artifact.content


def test_rework_loop_has_explicit_branch_and_return_geometry():
    ir = _compile("rework_loop.flo")
    request = build_sppm_elk_layout_request(
        ir,
        options=RenderOptions(diagram="sppm"),
    )
    result = execute_elk_layout(request, engine=run_elkjs_layout)

    rework_edges = [edge for edge in request.edges if edge.is_rework]
    assert [edge.rework_variant for edge in rework_edges] == ["branch", "return"]
    assert all(
        result.path_for(edge.source_id, edge.target_id) is not None
        for edge in rework_edges
    )
    assert (
        result.node_bounds["correct_request"].y_px
        > result.node_bounds["review_request"].y_px
    )
