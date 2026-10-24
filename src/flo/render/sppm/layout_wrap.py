"""SPPM-owned wrapped row placement and routing policy."""

from __future__ import annotations

from dataclasses import replace

from ..layout_core.elk_contracts import ElkLayoutRequest
from ..layout_core.models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    RoutedEdgePath,
)
from .wrapped_rework import align_rework_rows, choose_rework_rows, route_score


def _has_sppm_wrap_rows(*, request: ElkLayoutRequest) -> bool:
    return any(lane.id.startswith("__sppm_row_wrap_") for lane in request.lanes)


def _apply_sppm_wrap_rows(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> tuple[LayoutBounds, dict[str, LayoutLaneFrame]]:
    """Place wrapped SPPM rows and route cross-row edges through clear corridors."""

    def score_candidate(candidate: ElkLayoutRequest) -> tuple[int, int, int, float]:
        candidate_bounds = dict(node_bounds)
        candidate_paths = dict(edge_paths)
        rows, _frames = _place_sppm_wrap_rows(
            request=candidate,
            node_bounds=candidate_bounds,
            margin_px=12.0,
            horizontal_gap_px=56.0,
            vertical_gap_px=84.0,
        )
        _route_sppm_wrap_edges(
            request=candidate,
            node_bounds=candidate_bounds,
            edge_paths=candidate_paths,
            row_index_by_node=rows,
        )
        return route_score(candidate_bounds, candidate_paths)

    request = choose_rework_rows(request, score_candidate)
    margin_px = 12.0
    row_index_by_node, lane_frames = _place_sppm_wrap_rows(
        request=request,
        node_bounds=node_bounds,
        margin_px=margin_px,
        horizontal_gap_px=56.0,
        vertical_gap_px=84.0,
    )
    _route_sppm_wrap_edges(
        request=request,
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        row_index_by_node=row_index_by_node,
    )
    return (
        _wrapped_layout_bounds(
            node_bounds=node_bounds,
            edge_paths=edge_paths,
            margin_px=margin_px,
        ),
        lane_frames,
    )


def _place_sppm_wrap_rows(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    margin_px: float,
    horizontal_gap_px: float,
    vertical_gap_px: float,
) -> tuple[dict[str, int], dict[str, LayoutLaneFrame]]:
    y_px = margin_px
    row_index_by_node: dict[str, int] = {}
    lane_frames: dict[str, LayoutLaneFrame] = {}
    row_width_by_lane = {
        lane.id: sum(
            node_bounds[node_id].width_px
            for node_id in lane.node_ids
            if node_id in node_bounds
        )
        + horizontal_gap_px
        * max(0, sum(node_id in node_bounds for node_id in lane.node_ids) - 1)
        for lane in request.lanes
    }
    max_row_width = max(row_width_by_lane.values(), default=0.0)

    for row_index, lane in enumerate(request.lanes):
        row_node_ids = tuple(
            node_id for node_id in lane.node_ids if node_id in node_bounds
        )
        if not row_node_ids:
            continue
        row_height = max(node_bounds[node_id].height_px for node_id in row_node_ids)
        row_width = row_width_by_lane.get(lane.id, 0.0)
        row_offset = (
            max(0.0, max_row_width - row_width)
            if lane.id.startswith("__sppm_row_wrap_rework_")
            else 0.0
        )
        x_px = margin_px + row_offset
        for node_id in row_node_ids:
            bounds = node_bounds[node_id]
            node_bounds[node_id] = LayoutBounds(
                x_px=x_px,
                y_px=y_px + ((row_height - bounds.height_px) / 2.0),
                width_px=bounds.width_px,
                height_px=bounds.height_px,
            )
            row_index_by_node[node_id] = row_index
            x_px += bounds.width_px + horizontal_gap_px
        framed_row_width = x_px - horizontal_gap_px + margin_px
        lane_frames[lane.id] = LayoutLaneFrame(
            id=lane.id,
            label=lane.label,
            bounds=LayoutBounds(
                x_px=0.0,
                y_px=max(0.0, y_px - margin_px),
                width_px=framed_row_width,
                height_px=row_height + (margin_px * 2.0),
            ),
            node_ids=row_node_ids,
        )
        y_px += row_height + vertical_gap_px
    align_rework_rows(request, node_bounds)
    for lane_id, frame in lane_frames.items():
        lane_frames[lane_id] = replace(
            frame,
            bounds=replace(
                frame.bounds,
                width_px=max(
                    node_bounds[node].x_px + node_bounds[node].width_px
                    for node in frame.node_ids
                )
                + margin_px,
            ),
        )
    return row_index_by_node, lane_frames


def _route_sppm_wrap_edges(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    row_index_by_node: dict[str, int],
) -> None:
    bands = _wrapped_row_extents(node_bounds, row_index_by_node)
    edge_by_key = {(edge.source_id, edge.target_id): edge for edge in request.edges}
    node_kind_by_id = {node.id: node.kind for node in request.nodes}
    for edge_key in sorted(edge_by_key):
        source_id, target_id = edge_key
        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        if source_bounds is None or target_bounds is None:
            continue
        edge_spec = edge_by_key[edge_key]
        points, source_side, target_side = _wrapped_sppm_edge_points(
            source_bounds=source_bounds,
            target_bounds=target_bounds,
            source_kind=node_kind_by_id.get(source_id, "task"),
            target_kind=node_kind_by_id.get(target_id, "task"),
            source_row=row_index_by_node.get(source_id),
            target_row=row_index_by_node.get(target_id),
            is_rework=edge_spec.is_rework,
            rework_variant=edge_spec.rework_variant,
            source_band=bands.get(row_index_by_node.get(source_id)),
            target_band=bands.get(row_index_by_node.get(target_id)),
            outer_left=min(box.x_px for box in node_bounds.values()) - 8.0,
            outer_right=max(box.x_px + box.width_px for box in node_bounds.values())
            + 8.0,
        )
        edge_paths[edge_key] = RoutedEdgePath(
            edge=edge_key,
            points=points,
            label=edge_spec.label,
            label_point=None,
            source_port_side=source_side,
            target_port_side=target_side,
            is_rework=edge_spec.is_rework,
            rework_variant=edge_spec.rework_variant,
            callout_lines=edge_spec.callout_lines,
            callout_near_source=edge_spec.callout_near_source,
            outgoing_token=edge_spec.outgoing_token,
            incoming_token=edge_spec.incoming_token,
        )


def _wrapped_row_extents(node_bounds, rows):
    bands = {}
    for node, bounds in node_bounds.items():
        row = rows.get(node)
        top, bottom = bands.get(row, (bounds.y_px, bounds.y_px + bounds.height_px))
        bands[row] = (
            min(top, bounds.y_px),
            max(bottom, bounds.y_px + bounds.height_px),
        )
    return bands


def _wrapped_layout_bounds(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    margin_px: float,
) -> LayoutBounds:
    max_x = max(
        (bounds.x_px + bounds.width_px for bounds in node_bounds.values()),
        default=margin_px,
    )
    max_y = max(
        (bounds.y_px + bounds.height_px for bounds in node_bounds.values()),
        default=margin_px,
    )
    for path in edge_paths.values():
        for point in path.points:
            max_x = max(max_x, point.x_px)
            max_y = max(max_y, point.y_px)
    return LayoutBounds(
        x_px=0.0,
        y_px=0.0,
        width_px=max_x + margin_px,
        height_px=max_y + margin_px,
    )


def _wrapped_sppm_edge_points(
    *,
    source_bounds: LayoutBounds,
    target_bounds: LayoutBounds,
    source_kind: str,
    target_kind: str,
    source_row: int | None,
    target_row: int | None,
    is_rework: bool,
    rework_variant: str | None,
    outer_left: float = 4.0,
    outer_right: float = 1200.0,
    source_band: tuple[float, float] | None = None,
    target_band: tuple[float, float] | None = None,
) -> tuple[tuple[LayoutPoint, ...], str, str]:
    if source_row == target_row and source_bounds.x_px < target_bounds.x_px:
        source = _wrapped_sppm_anchor(
            bounds=source_bounds,
            kind=source_kind,
            side="EAST",
        )
        target = _wrapped_sppm_anchor(
            bounds=target_bounds,
            kind=target_kind,
            side="WEST",
        )
        mid_x = (source.x_px + target.x_px) / 2.0
        return (
            (
                source,
                LayoutPoint(x_px=mid_x, y_px=source.y_px),
                LayoutPoint(x_px=mid_x, y_px=target.y_px),
                target,
            ),
            "EAST",
            "WEST",
        )

    upward = target_bounds.y_px < source_bounds.y_px
    source_side, target_side = ("NORTH", "SOUTH") if upward else ("SOUTH", "NORTH")
    source = _wrapped_sppm_anchor(
        bounds=source_bounds, kind=source_kind, side=source_side
    )
    target = _wrapped_sppm_anchor(
        bounds=target_bounds, kind=target_kind, side=target_side
    )
    source_top, source_bottom = source_band or (
        source_bounds.y_px,
        source_bounds.y_px + source_bounds.height_px,
    )
    target_top, target_bottom = target_band or (
        target_bounds.y_px,
        target_bounds.y_px + target_bounds.height_px,
    )
    source_clear = source_top if upward else source_bottom
    target_clear = target_bottom if upward else target_top
    corridor_y = (source_clear + target_clear) / 2.0
    if (
        source_row is not None
        and target_row is not None
        and abs(source_row - target_row) > 1
    ):
        # A skipped row may contain correction nodes or ordinary work. Route
        # outside the entire row envelope instead of through its contents.
        gutter = min(
            (outer_left, outer_right),
            key=lambda x: (abs(source.x_px - x) + abs(target.x_px - x), x),
        )
        source_y = source_clear + (-24.0 if upward else 24.0)
        target_y = target_clear + (24.0 if upward else -24.0)
        return (
            (
                source,
                LayoutPoint(source.x_px, source_y),
                LayoutPoint(gutter, source_y),
                LayoutPoint(gutter, target_y),
                LayoutPoint(target.x_px, target_y),
                target,
            ),
            source_side,
            target_side,
        )
    return (
        (
            source,
            LayoutPoint(source.x_px, corridor_y),
            LayoutPoint(target.x_px, corridor_y),
            target,
        ),
        source_side,
        target_side,
    )


def _wrapped_sppm_anchor(*, bounds: LayoutBounds, kind: str, side: str) -> LayoutPoint:
    center_x = bounds.x_px + (bounds.width_px / 2.0)
    center_y = bounds.y_px + (bounds.height_px / 2.0)
    if side == "NORTH":
        return LayoutPoint(x_px=center_x, y_px=bounds.y_px)
    if side == "SOUTH":
        return LayoutPoint(x_px=center_x, y_px=bounds.y_px + bounds.height_px)
    if side == "EAST":
        x_px = bounds.x_px + bounds.width_px
        if kind == "queue":
            x_px = bounds.x_px + (bounds.width_px * 0.75)
        return LayoutPoint(x_px=x_px, y_px=center_y)
    x_px = bounds.x_px
    if kind == "queue":
        x_px = bounds.x_px + (bounds.width_px * 0.25)
    return LayoutPoint(x_px=x_px, y_px=center_y)
