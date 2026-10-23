"""SPPM-owned queue spacing and mainline layout adjustments."""

from __future__ import annotations

import itertools
import statistics
from collections.abc import Callable
from dataclasses import replace

from ..layout_core.elk_contracts import ElkLayoutRequest
from ..layout_core.models import (
    LayoutBounds,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from ..layout_core.rework_geometry import infer_rework_row_ids, translate_edge_points


def _balance_sppm_queue_task_gaps(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> None:
    node_ids = set(node_bounds)
    mainline_ids, _rework_ids = _infer_sppm_row_ids_from_request(
        request=request,
        node_ids=node_ids,
    )
    if len(mainline_ids) < 3:
        return

    node_kind_by_id = {node.id: str(node.kind or "").lower() for node in request.nodes}
    direct_edges = {
        (edge.source_id, edge.target_id) for edge in request.edges if not edge.is_rework
    }

    incoming_by_target, outgoing_by_source = _mainline_direct_adjacency(
        mainline_ids=mainline_ids,
        direct_edges=direct_edges,
    )

    shifts: dict[str, tuple[float, float]] = {}

    def _is_queue(node_id: str) -> bool:
        return _is_queue_node(node_id=node_id, node_kind_by_id=node_kind_by_id)

    for queue_id in sorted(mainline_ids, key=lambda node_id: node_bounds[node_id].x_px):
        if not _is_queue(queue_id):
            continue
        incoming = incoming_by_target.get(queue_id, [])
        outgoing = outgoing_by_source.get(queue_id, [])
        shift = _queue_gap_shift(
            queue_id=queue_id,
            incoming=incoming,
            outgoing=outgoing,
            node_bounds=node_bounds,
            is_queue=_is_queue,
        )
        if shift is not None:
            shifts[queue_id] = (shift, 0.0)

    if not shifts:
        return

    _apply_layout_shifts(
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        shifts=shifts,
    )


def _is_queue_node(*, node_id: str, node_kind_by_id: dict[str, str]) -> bool:
    kind = str(node_kind_by_id.get(node_id, "")).lower()
    return kind == "queue" if kind else ("queue" in node_id.lower())


def _mainline_direct_adjacency(
    *,
    mainline_ids: set[str],
    direct_edges: set[tuple[str, str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    incoming_by_target: dict[str, list[str]] = {node_id: [] for node_id in mainline_ids}
    outgoing_by_source: dict[str, list[str]] = {node_id: [] for node_id in mainline_ids}
    for source_id, target_id in direct_edges:
        if source_id not in mainline_ids or target_id not in mainline_ids:
            continue
        incoming_by_target[target_id].append(source_id)
        outgoing_by_source[source_id].append(target_id)
    return incoming_by_target, outgoing_by_source


def _queue_gap_shift(
    *,
    queue_id: str,
    incoming: list[str],
    outgoing: list[str],
    node_bounds: dict[str, LayoutBounds],
    is_queue: Callable[[str], bool],
) -> float | None:
    if len(incoming) != 1 or len(outgoing) != 1:
        return None

    upstream_id = incoming[0]
    downstream_id = outgoing[0]
    if not is_queue(upstream_id) or is_queue(downstream_id):
        return None
    if upstream_id not in node_bounds or downstream_id not in node_bounds:
        return None

    upstream_right = node_bounds[upstream_id].x_px + node_bounds[upstream_id].width_px
    queue_left = node_bounds[queue_id].x_px
    queue_width = node_bounds[queue_id].width_px
    downstream_left = node_bounds[downstream_id].x_px

    gap_left = queue_left - upstream_right
    gap_right = downstream_left - (queue_left + queue_width)
    if gap_left <= 0.0 or gap_right <= 0.0:
        return None
    if gap_right <= (gap_left * 1.6):
        return None

    target_queue_left = (downstream_left + upstream_right - queue_width) / 2.0
    min_gap_px = 56.0
    target_queue_left = max(target_queue_left, upstream_right + min_gap_px)
    target_queue_left = min(
        target_queue_left,
        downstream_left - queue_width - min_gap_px,
    )
    if target_queue_left <= upstream_right:
        return None
    if target_queue_left + queue_width >= downstream_left:
        return None
    return target_queue_left - queue_left


def _normalize_sppm_mainline_horizontal_spacing(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> None:
    mainline_ids, _rework_ids = _infer_sppm_row_ids_from_request(
        request=request,
        node_ids=set(node_bounds),
    )
    ordered = sorted(mainline_ids, key=lambda node_id: node_bounds[node_id].x_px)
    if len(ordered) < 3:
        return

    gaps: list[float] = []
    for left_id, right_id in itertools.pairwise(ordered):
        left_bounds = node_bounds[left_id]
        right_bounds = node_bounds[right_id]
        gap = right_bounds.x_px - (left_bounds.x_px + left_bounds.width_px)
        if gap > 0.0:
            gaps.append(gap)
    if len(gaps) < 2:
        return

    target_gap = max(56.0, float(statistics.median(gaps)))
    if max(gaps) <= (target_gap * 1.25) and min(gaps) >= (target_gap * 0.75):
        return

    shifts: dict[str, tuple[float, float]] = {}
    propagated_dx = 0.0
    for left_id, right_id in itertools.pairwise(ordered):
        left_dx = shifts.get(left_id, (0.0, 0.0))[0]
        right_dx, right_dy = shifts.get(right_id, (0.0, 0.0))
        left_right = node_bounds[left_id].x_px + left_dx + node_bounds[left_id].width_px
        right_left = node_bounds[right_id].x_px + right_dx + propagated_dx
        propagated_dx += (left_right + target_gap) - right_left
        shifts[right_id] = (right_dx + propagated_dx, right_dy)

    _apply_layout_shifts(
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        shifts=shifts,
    )


def _apply_layout_shifts(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    shifts: dict[str, tuple[float, float]],
) -> None:
    if not shifts:
        return

    for node_id, (dx, dy) in shifts.items():
        bounds = node_bounds[node_id]
        node_bounds[node_id] = LayoutBounds(
            x_px=bounds.x_px + dx,
            y_px=bounds.y_px + dy,
            width_px=bounds.width_px,
            height_px=bounds.height_px,
        )

    for edge_key, edge_path in tuple(edge_paths.items()):
        source_id, target_id = edge_key
        source_shift = shifts.get(source_id, (0.0, 0.0))
        target_shift = shifts.get(target_id, (0.0, 0.0))
        if source_shift == (0.0, 0.0) and target_shift == (0.0, 0.0):
            continue
        shifted_label_point = edge_path.label_point
        if shifted_label_point is not None:
            lx = shifted_label_point.x_px + ((source_shift[0] + target_shift[0]) / 2.0)
            ly = shifted_label_point.y_px + ((source_shift[1] + target_shift[1]) / 2.0)
            shifted_label_point = LayoutPoint(x_px=lx, y_px=ly)
        edge_paths[edge_key] = replace(
            edge_path,
            points=translate_edge_points(
                edge_path.points,
                source_shift=source_shift,
                target_shift=target_shift,
            ),
            label_point=shifted_label_point,
        )


def _infer_sppm_row_ids_from_request(
    *,
    request: ElkLayoutRequest,
    node_ids: set[str],
) -> tuple[set[str], set[str]]:
    return infer_rework_row_ids(
        node_ids=node_ids,
        edges=(
            (
                edge.source_id,
                edge.target_id,
                edge.is_rework,
                edge.rework_variant,
            )
            for edge in request.edges
        ),
    )


def transform_sppm_layout(
    request: ElkLayoutRequest, result: LayoutResult
) -> LayoutResult:
    """Apply SPPM conventions to normalized engine coordinates."""
    from .layout_wrap import _apply_sppm_wrap_rows, _has_sppm_wrap_rows

    bounds, paths = dict(result.node_bounds), dict(result.edge_paths)
    _balance_sppm_queue_task_gaps(request=request, node_bounds=bounds, edge_paths=paths)
    _normalize_sppm_mainline_horizontal_spacing(
        request=request, node_bounds=bounds, edge_paths=paths
    )
    canvas, lanes = result.canvas_bounds, result.lanes
    if _has_sppm_wrap_rows(request=request):
        canvas, frames = _apply_sppm_wrap_rows(
            request=request, node_bounds=bounds, edge_paths=paths
        )
        lanes = tuple(frames.values())
    return replace(
        result, canvas_bounds=canvas, node_bounds=bounds, edge_paths=paths, lanes=lanes
    )
