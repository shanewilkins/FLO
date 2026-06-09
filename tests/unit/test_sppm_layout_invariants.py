from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from statistics import fmean

import pytest

from flo.adapters import parse_adapter
from flo.render.layout_core import (
    ElkLayoutEdge,
    ElkLayoutNode,
    ElkLayoutRequest,
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
    build_sppm_elk_layout_request,
    execute_elk_layout,
    run_elkjs_layout,
)
from flo.render.options import RenderOptions

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORPUS_PATH = _REPO_ROOT / "examples" / "conformance" / "sppm_corpus.json"


def _load_corpus() -> dict[str, dict[str, object]]:
    raw = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    cases = raw.get("cases", []) if isinstance(raw, dict) else []
    out: dict[str, dict[str, object]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        if isinstance(case_id, str) and case_id:
            out[case_id] = case
    return out


_CORPUS_BY_ID = _load_corpus()


@lru_cache(maxsize=None)
def _request_and_result(case_id: str) -> tuple[ElkLayoutRequest, LayoutResult]:
    case = _CORPUS_BY_ID[case_id]
    source_rel = str(case["input"])
    source_path = _REPO_ROOT / source_rel
    options_map = {"diagram": "sppm", **dict(case.get("options", {}))}
    options = RenderOptions.from_mapping(options_map)

    model = parse_adapter(
        source_path.read_text(encoding="utf-8"),
        source_path=str(source_path),
    )
    request = build_sppm_elk_layout_request(model, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    return request, result


def _major_center(bounds: LayoutBounds, direction: str) -> float:
    return (
        bounds.y_px + (bounds.height_px / 2.0)
        if direction == "DOWN"
        else bounds.x_px + (bounds.width_px / 2.0)
    )


def _cross_center(bounds: LayoutBounds, direction: str) -> float:
    return (
        bounds.x_px + (bounds.width_px / 2.0)
        if direction == "DOWN"
        else bounds.y_px + (bounds.height_px / 2.0)
    )


def _branch_targets(request: ElkLayoutRequest) -> set[str]:
    return {edge.target_id for edge in request.edges if edge.rework_variant == "branch"}


def _return_sources(request: ElkLayoutRequest) -> set[str]:
    return {edge.source_id for edge in request.edges if edge.rework_variant == "return"}


def _non_rework_adjacency(request: ElkLayoutRequest) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node.id: [] for node in request.nodes}
    for edge in request.edges:
        if edge.is_rework:
            continue
        if edge.source_id in adjacency:
            adjacency[edge.source_id].append(edge.target_id)
    return adjacency


def _rework_node_ids(request: ElkLayoutRequest) -> set[str]:
    rework: set[str] = set()
    frontier = list(_branch_targets(request))
    return_sources = _return_sources(request)
    adjacency = _non_rework_adjacency(request)
    while frontier:
        current = frontier.pop()
        if current in rework:
            continue
        rework.add(current)
        if current in return_sources:
            continue
        for nxt in adjacency.get(current, []):
            if nxt not in rework:
                frontier.append(nxt)
    return rework


def _mainline_node_ids(request: ElkLayoutRequest) -> set[str]:
    return {node.id for node in request.nodes} - _rework_node_ids(request)


def _interval_distance(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower - value
    if value > upper:
        return value - upper
    return 0.0


def _distance_to_side(
    point: LayoutPoint, bounds: LayoutBounds, side: str | None
) -> float:
    if side == "NORTH":
        return abs(point.y_px - bounds.y_px) + _interval_distance(
            point.x_px, bounds.x_px, bounds.x_px + bounds.width_px
        )
    if side == "SOUTH":
        y = bounds.y_px + bounds.height_px
        return abs(point.y_px - y) + _interval_distance(
            point.x_px, bounds.x_px, bounds.x_px + bounds.width_px
        )
    if side == "WEST":
        return abs(point.x_px - bounds.x_px) + _interval_distance(
            point.y_px, bounds.y_px, bounds.y_px + bounds.height_px
        )
    if side == "EAST":
        x = bounds.x_px + bounds.width_px
        return abs(point.x_px - x) + _interval_distance(
            point.y_px, bounds.y_px, bounds.y_px + bounds.height_px
        )
    return 0.0


def _assert_mainline_monotonic(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    min_major_step_px: float = 20.0,
) -> None:
    mainline = _mainline_node_ids(request)
    node_by_id = {node.id: node for node in request.nodes}
    forward_deltas: list[tuple[str, str, int, int, float]] = []
    for edge in request.edges:
        if edge.is_rework:
            continue
        if edge.source_id not in mainline or edge.target_id not in mainline:
            continue
        source_node = node_by_id.get(edge.source_id)
        target_node = node_by_id.get(edge.target_id)
        if source_node is None or target_node is None:
            continue
        if source_node.partition_index is None or target_node.partition_index is None:
            continue
        if target_node.partition_index <= source_node.partition_index:
            # Feedback and same-partition edges are allowed to break monotonic flow.
            continue

        source_bounds = result.bounds_for(edge.source_id)
        target_bounds = result.bounds_for(edge.target_id)
        if source_bounds is None or target_bounds is None:
            continue
        delta = _major_center(target_bounds, request.direction) - _major_center(
            source_bounds, request.direction
        )
        forward_deltas.append(
            (
                edge.source_id,
                edge.target_id,
                source_node.partition_index,
                target_node.partition_index,
                delta,
            )
        )

    for (
        source_id,
        target_id,
        source_partition,
        target_partition,
        delta,
    ) in forward_deltas:
        assert abs(delta) >= min_major_step_px, (
            "mainline_monotonic violated: "
            f"edge {source_id}->{target_id} "
            f"partition {source_partition}->{target_partition} "
            f"delta_major={delta:.2f}px"
        )


def _assert_rework_separation(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    min_cross_separation_px: float = 40.0,
) -> None:
    rework = _rework_node_ids(request)
    if not rework:
        return
    mainline = _mainline_node_ids(request)
    if not mainline:
        return

    mainline_cross = [
        _cross_center(bounds, request.direction)
        for node_id in sorted(mainline)
        if (bounds := result.bounds_for(node_id)) is not None
    ]
    rework_cross = [
        _cross_center(bounds, request.direction)
        for node_id in sorted(rework)
        if (bounds := result.bounds_for(node_id)) is not None
    ]
    if not mainline_cross or not rework_cross:
        return

    separation = abs(fmean(rework_cross) - fmean(mainline_cross))
    assert separation >= min_cross_separation_px, (
        f"rework_row_separation violated: cross_center_delta={separation:.2f}px"
    )


def _assert_rework_edge_attachments(
    request: ElkLayoutRequest,
    result: LayoutResult,
    *,
    max_side_distance_px: float = 8.0,
) -> None:
    for edge in request.edges:
        if edge.rework_variant not in {"branch", "return"}:
            continue

        path = result.path_for(edge.source_id, edge.target_id)
        assert path is not None, (
            f"rework_attachment violated: missing path {edge.source_id}->{edge.target_id}"
        )
        if not path.points:
            raise AssertionError(
                f"rework_attachment violated: empty path {edge.source_id}->{edge.target_id}"
            )

        source_bounds = result.bounds_for(edge.source_id)
        target_bounds = result.bounds_for(edge.target_id)
        assert source_bounds is not None
        assert target_bounds is not None

        source_side = path.source_port_side or edge.source_port_side
        target_side = path.target_port_side or edge.target_port_side

        source_distance = _distance_to_side(path.points[0], source_bounds, source_side)
        target_distance = _distance_to_side(path.points[-1], target_bounds, target_side)

        assert source_distance <= max_side_distance_px, (
            f"rework_attachment violated: {edge.source_id}->{edge.target_id} "
            f"source side={source_side} distance={source_distance:.2f}px"
        )
        assert target_distance <= max_side_distance_px, (
            f"rework_attachment violated: {edge.source_id}->{edge.target_id} "
            f"target side={target_side} distance={target_distance:.2f}px"
        )


@pytest.mark.parametrize("case_id", sorted(_CORPUS_BY_ID.keys()))
def test_sppm_corpus_layout_invariants_hold(case_id: str):
    request, result = _request_and_result(case_id)
    _assert_mainline_monotonic(request, result)
    _assert_rework_separation(request, result)
    _assert_rework_edge_attachments(request, result)


def test_mainline_monotonic_reports_negative_case():
    request = ElkLayoutRequest(
        diagram="sppm",
        direction="RIGHT",
        lanes=(),
        nodes=(
            ElkLayoutNode(
                id="a",
                label="A",
                kind="task",
                width_px=100,
                height_px=40,
                partition_index=0,
            ),
            ElkLayoutNode(
                id="b",
                label="B",
                kind="task",
                width_px=100,
                height_px=40,
                partition_index=1,
            ),
            ElkLayoutNode(
                id="c",
                label="C",
                kind="task",
                width_px=100,
                height_px=40,
                partition_index=2,
            ),
        ),
        edges=(
            ElkLayoutEdge(id="e0", source_id="a", target_id="b", is_rework=False),
            ElkLayoutEdge(id="e1", source_id="b", target_id="c", is_rework=False),
        ),
    )
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=300, height_px=200),
        node_bounds={
            "a": LayoutBounds(x_px=20, y_px=40, width_px=100, height_px=40),
            "b": LayoutBounds(x_px=24, y_px=40, width_px=100, height_px=40),
            "c": LayoutBounds(x_px=28, y_px=40, width_px=100, height_px=40),
        },
        edge_paths={
            ("a", "b"): RoutedEdgePath(
                edge=("a", "b"),
                points=(LayoutPoint(x_px=120, y_px=60), LayoutPoint(x_px=24, y_px=60)),
            ),
            ("b", "c"): RoutedEdgePath(
                edge=("b", "c"),
                points=(LayoutPoint(x_px=124, y_px=60), LayoutPoint(x_px=28, y_px=60)),
            ),
        },
    )

    with pytest.raises(AssertionError, match="mainline_monotonic violated"):
        _assert_mainline_monotonic(request, result, min_major_step_px=20.0)


def test_rework_row_separation_reports_negative_case():
    request = ElkLayoutRequest(
        diagram="sppm",
        direction="RIGHT",
        lanes=(),
        nodes=(
            ElkLayoutNode(
                id="decision",
                label="Decision",
                kind="decision",
                width_px=120,
                height_px=60,
            ),
            ElkLayoutNode(
                id="mainline", label="Mainline", kind="task", width_px=120, height_px=50
            ),
            ElkLayoutNode(
                id="rework", label="Rework", kind="task", width_px=120, height_px=50
            ),
        ),
        edges=(
            ElkLayoutEdge(id="e0", source_id="decision", target_id="mainline"),
            ElkLayoutEdge(
                id="e1",
                source_id="decision",
                target_id="rework",
                is_rework=True,
                rework_variant="branch",
            ),
        ),
    )
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=500, height_px=200),
        node_bounds={
            "decision": LayoutBounds(x_px=20, y_px=50, width_px=120, height_px=60),
            "mainline": LayoutBounds(x_px=200, y_px=52, width_px=120, height_px=50),
            "rework": LayoutBounds(x_px=200, y_px=55, width_px=120, height_px=50),
        },
        edge_paths={
            ("decision", "mainline"): RoutedEdgePath(
                edge=("decision", "mainline"),
                points=(LayoutPoint(x_px=140, y_px=80), LayoutPoint(x_px=200, y_px=80)),
            ),
            ("decision", "rework"): RoutedEdgePath(
                edge=("decision", "rework"),
                points=(LayoutPoint(x_px=80, y_px=110), LayoutPoint(x_px=200, y_px=80)),
                is_rework=True,
                rework_variant="branch",
                source_port_side="SOUTH",
                target_port_side="NORTH",
            ),
        },
    )

    with pytest.raises(AssertionError, match="rework_row_separation violated"):
        _assert_rework_separation(request, result, min_cross_separation_px=40.0)


def test_rework_attachment_reports_negative_case():
    request = ElkLayoutRequest(
        diagram="sppm",
        direction="RIGHT",
        lanes=(),
        nodes=(
            ElkLayoutNode(
                id="decision",
                label="Decision",
                kind="decision",
                width_px=100,
                height_px=60,
            ),
            ElkLayoutNode(
                id="rework", label="Rework", kind="task", width_px=120, height_px=50
            ),
        ),
        edges=(
            ElkLayoutEdge(
                id="e0",
                source_id="decision",
                target_id="rework",
                is_rework=True,
                rework_variant="branch",
                source_port_side="SOUTH",
                target_port_side="NORTH",
            ),
        ),
    )
    result = LayoutResult(
        orientation="lr",
        canvas_bounds=LayoutBounds(x_px=0, y_px=0, width_px=400, height_px=220),
        node_bounds={
            "decision": LayoutBounds(x_px=20, y_px=40, width_px=100, height_px=60),
            "rework": LayoutBounds(x_px=220, y_px=140, width_px=120, height_px=50),
        },
        edge_paths={
            ("decision", "rework"): RoutedEdgePath(
                edge=("decision", "rework"),
                points=(LayoutPoint(x_px=10, y_px=40), LayoutPoint(x_px=200, y_px=120)),
                is_rework=True,
                rework_variant="branch",
                source_port_side="SOUTH",
                target_port_side="NORTH",
            )
        },
    )

    with pytest.raises(AssertionError, match="rework_attachment violated"):
        _assert_rework_edge_attachments(request, result, max_side_distance_px=8.0)
