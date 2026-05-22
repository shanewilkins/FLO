"""Row alignment and canvas geometry helpers for direct SPPM SVG rendering."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .layout_core.models import LayoutBounds, LayoutPoint


def _enforce_sppm_row_alignment(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], Any],
    lanes: tuple[Any, ...],
) -> tuple[dict[str, LayoutBounds], dict[tuple[str, str], Any]]:
    mainline_ids, rework_ids = _sppm_row_ids(lanes=lanes, node_bounds=node_bounds)
    if not mainline_ids or not rework_ids:
        return dict(node_bounds), _orthogonalized_edges(edge_paths=edge_paths)

    shifts = _initial_row_shifts(
        node_bounds=node_bounds,
        mainline_ids=mainline_ids,
        rework_ids=rework_ids,
    )
    _align_rework_clusters(
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        mainline_ids=mainline_ids,
        rework_ids=rework_ids,
        shifts=shifts,
    )
    _enforce_mainline_min_horizontal_gap(
        node_bounds=node_bounds,
        mainline_ids=mainline_ids,
        shifts=shifts,
    )
    _clamp_shifted_nodes_between_terminals(node_bounds=node_bounds, shifts=shifts)

    transformed_nodes = _apply_node_shifts(node_bounds=node_bounds, shifts=shifts)
    transformed_edges = _apply_edge_shifts(edge_paths=edge_paths, shifts=shifts)
    return transformed_nodes, transformed_edges


def _display_canvas_bounds(
    *,
    base_canvas: LayoutBounds,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], Any],
) -> LayoutBounds:
    max_x = base_canvas.x_px + base_canvas.width_px
    max_y = base_canvas.y_px + base_canvas.height_px
    for bounds in node_bounds.values():
        max_x = max(max_x, bounds.x_px + bounds.width_px)
        max_y = max(max_y, bounds.y_px + bounds.height_px)
    for edge_path in edge_paths.values():
        for point in edge_path.points:
            max_x = max(max_x, point.x_px)
            max_y = max(max_y, point.y_px)
    return LayoutBounds(
        x_px=base_canvas.x_px,
        y_px=base_canvas.y_px,
        width_px=max_x - base_canvas.x_px,
        height_px=max_y - base_canvas.y_px,
    )


def _sppm_row_ids(
    *,
    lanes: tuple[Any, ...],
    node_bounds: dict[str, LayoutBounds],
) -> tuple[set[str], set[str]]:
    mainline_ids: set[str] = set()
    rework_ids: set[str] = set()
    for lane in lanes:
        lane_id = str(getattr(lane, "id", ""))
        lane_node_ids = {
            str(node_id)
            for node_id in getattr(lane, "node_ids", ())
            if str(node_id) in node_bounds
        }
        if lane_id == "__sppm_row_mainline":
            mainline_ids.update(lane_node_ids)
        elif lane_id == "__sppm_row_rework":
            rework_ids.update(lane_node_ids)
    return mainline_ids, rework_ids


def _orthogonalized_edges(
    *, edge_paths: dict[tuple[str, str], Any]
) -> dict[tuple[str, str], Any]:
    return {
        edge_key: replace(edge_path, points=_orthogonalize_points(edge_path.points))
        for edge_key, edge_path in edge_paths.items()
    }


def _initial_row_shifts(
    *,
    node_bounds: dict[str, LayoutBounds],
    mainline_ids: set[str],
    rework_ids: set[str],
) -> dict[str, tuple[float, float]]:
    shifts: dict[str, tuple[float, float]] = {
        node_id: (0.0, 0.0) for node_id in node_bounds
    }
    mainline_center_y = sum(
        node_bounds[node_id].y_px + (node_bounds[node_id].height_px / 2.0)
        for node_id in mainline_ids
    ) / float(len(mainline_ids))
    max_mainline_height = max(
        node_bounds[node_id].height_px for node_id in mainline_ids
    )
    max_rework_height = max(node_bounds[node_id].height_px for node_id in rework_ids)
    rework_center_y = (
        mainline_center_y
        + (max_mainline_height / 2.0)
        + (max_rework_height / 2.0)
        + 96.0
    )
    for node_id in mainline_ids:
        bounds = node_bounds[node_id]
        center_y = bounds.y_px + (bounds.height_px / 2.0)
        shifts[node_id] = (0.0, mainline_center_y - center_y)
    for node_id in rework_ids:
        bounds = node_bounds[node_id]
        center_y = bounds.y_px + (bounds.height_px / 2.0)
        shifts[node_id] = (0.0, rework_center_y - center_y)
    return shifts


def _align_rework_clusters(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], Any],
    mainline_ids: set[str],
    rework_ids: set[str],
    shifts: dict[str, tuple[float, float]],
) -> None:
    rework_adjacency, branch_pairs = _rework_graph(
        edge_paths=edge_paths,
        mainline_ids=mainline_ids,
        rework_ids=rework_ids,
    )
    visited_rework_ids: set[str] = set()
    rework_spacing = max(
        220.0,
        max(node_bounds[node_id].width_px for node_id in rework_ids) + 56.0,
    )
    sorted_pairs = sorted(
        branch_pairs,
        key=lambda pair: (
            node_bounds[pair[0]].x_px + (node_bounds[pair[0]].width_px / 2.0)
        ),
    )
    for source_id, target_id in sorted_pairs:
        if target_id in visited_rework_ids:
            continue
        cluster = _connected_cluster(seed=target_id, adjacency=rework_adjacency)
        if not cluster:
            continue
        ordered_cluster = _ordered_cluster(
            target_id=target_id,
            cluster=cluster,
            adjacency=rework_adjacency,
            node_bounds=node_bounds,
        )
        source_center_x = node_bounds[source_id].x_px + (
            node_bounds[source_id].width_px / 2.0
        )
        for index, node_id in enumerate(ordered_cluster):
            bounds = node_bounds[node_id]
            current_center_x = bounds.x_px + (bounds.width_px / 2.0)
            target_center_x = source_center_x - (index * rework_spacing)
            _, dy = shifts.get(node_id, (0.0, 0.0))
            shifts[node_id] = (target_center_x - current_center_x, dy)
        visited_rework_ids.update(cluster)


def _rework_graph(
    *,
    edge_paths: dict[tuple[str, str], Any],
    mainline_ids: set[str],
    rework_ids: set[str],
) -> tuple[dict[str, set[str]], list[tuple[str, str]]]:
    rework_adjacency: dict[str, set[str]] = {node_id: set() for node_id in rework_ids}
    branch_pairs: list[tuple[str, str]] = []
    for (source_id, target_id), edge_path in edge_paths.items():
        if (
            source_id in rework_ids
            and target_id in rework_ids
            and not bool(edge_path.is_rework)
        ):
            rework_adjacency[source_id].add(target_id)
            rework_adjacency[target_id].add(source_id)
        if (
            str(edge_path.rework_variant or "") == "branch"
            and source_id in mainline_ids
            and target_id in rework_ids
        ):
            branch_pairs.append((source_id, target_id))
    return rework_adjacency, branch_pairs


def _connected_cluster(*, seed: str, adjacency: dict[str, set[str]]) -> set[str]:
    cluster: set[str] = set()
    stack = [seed]
    while stack:
        current = stack.pop()
        if current in cluster:
            continue
        cluster.add(current)
        for neighbor in adjacency.get(current, set()):
            if neighbor not in cluster:
                stack.append(neighbor)
    return cluster


def _ordered_cluster(
    *,
    target_id: str,
    cluster: set[str],
    adjacency: dict[str, set[str]],
    node_bounds: dict[str, LayoutBounds],
) -> list[str]:
    ordered_cluster: list[str] = [target_id]
    while True:
        current = ordered_cluster[-1]
        next_ids = sorted(
            (
                node_id
                for node_id in adjacency.get(current, set())
                if node_id in cluster and node_id not in ordered_cluster
            ),
            key=lambda node_id: node_bounds[node_id].x_px,
        )
        if not next_ids:
            break
        ordered_cluster.append(next_ids[0])
    for node_id in sorted(cluster):
        if node_id not in ordered_cluster:
            ordered_cluster.append(node_id)
    return ordered_cluster


def _clamp_shifted_nodes_between_terminals(
    *,
    node_bounds: dict[str, LayoutBounds],
    shifts: dict[str, tuple[float, float]],
) -> None:
    start_id = "start" if "start" in node_bounds else None
    stop_id = (
        "stop"
        if "stop" in node_bounds
        else (
            "end"
            if "end" in node_bounds
            else ("finish" if "finish" in node_bounds else None)
        )
    )
    if start_id is None or stop_id is None:
        return
    start_bounds = node_bounds[start_id]
    stop_bounds = node_bounds[stop_id]
    min_center_x = start_bounds.x_px + (start_bounds.width_px / 2.0)
    max_center_x = stop_bounds.x_px + (stop_bounds.width_px / 2.0)
    if min_center_x > max_center_x:
        return
    for node_id, bounds in node_bounds.items():
        if node_id in {start_id, stop_id}:
            continue
        dx, dy = shifts.get(node_id, (0.0, 0.0))
        center_x = bounds.x_px + (bounds.width_px / 2.0) + dx
        if center_x < min_center_x:
            dx += min_center_x - center_x
        elif center_x > max_center_x:
            dx += max_center_x - center_x
        shifts[node_id] = (dx, dy)


def _apply_node_shifts(
    *,
    node_bounds: dict[str, LayoutBounds],
    shifts: dict[str, tuple[float, float]],
) -> dict[str, LayoutBounds]:
    transformed_nodes: dict[str, LayoutBounds] = {}
    for node_id, bounds in node_bounds.items():
        dx, dy = shifts.get(node_id, (0.0, 0.0))
        transformed_nodes[node_id] = LayoutBounds(
            x_px=bounds.x_px + dx,
            y_px=bounds.y_px + dy,
            width_px=bounds.width_px,
            height_px=bounds.height_px,
        )
    return transformed_nodes


def _apply_edge_shifts(
    *,
    edge_paths: dict[tuple[str, str], Any],
    shifts: dict[str, tuple[float, float]],
) -> dict[tuple[str, str], Any]:
    transformed_edges: dict[tuple[str, str], Any] = {}
    for edge_key, edge_path in edge_paths.items():
        source_id, target_id = edge_key
        source_shift = shifts.get(source_id, (0.0, 0.0))
        target_shift = shifts.get(target_id, (0.0, 0.0))
        translated_points = _translate_edge_points(
            edge_path.points,
            source_shift=source_shift,
            target_shift=target_shift,
        )
        transformed_edges[edge_key] = replace(
            edge_path,
            points=_orthogonalize_points(translated_points),
        )
    return transformed_edges


def _enforce_mainline_min_horizontal_gap(
    *,
    node_bounds: dict[str, LayoutBounds],
    mainline_ids: set[str],
    shifts: dict[str, tuple[float, float]],
) -> None:
    ordered_mainline = sorted(
        mainline_ids, key=lambda node_id: node_bounds[node_id].x_px
    )
    if len(ordered_mainline) < 2:
        return

    min_gap_px = 56.0
    propagated_dx = 0.0
    for prev_id, current_id in zip(ordered_mainline, ordered_mainline[1:]):
        prev_dx, _ = shifts.get(prev_id, (0.0, 0.0))
        current_dx, current_dy = shifts.get(current_id, (0.0, 0.0))
        prev_right = node_bounds[prev_id].x_px + prev_dx + node_bounds[prev_id].width_px
        current_left = node_bounds[current_id].x_px + current_dx + propagated_dx
        deficit = (prev_right + min_gap_px) - current_left
        if deficit > 0.0:
            propagated_dx += deficit
        shifts[current_id] = (current_dx + propagated_dx, current_dy)


def _translate_edge_points(
    points: tuple[LayoutPoint, ...],
    *,
    source_shift: tuple[float, float],
    target_shift: tuple[float, float],
) -> tuple[LayoutPoint, ...]:
    if not points:
        return points
    sx, sy = source_shift
    tx, ty = target_shift
    if abs(sx - tx) < 1e-9 and abs(sy - ty) < 1e-9:
        return tuple(
            LayoutPoint(x_px=point.x_px + sx, y_px=point.y_px + sy) for point in points
        )

    distances = [0.0]
    total = 0.0
    for index in range(len(points) - 1):
        p0 = points[index]
        p1 = points[index + 1]
        seg_len = ((p1.x_px - p0.x_px) ** 2 + (p1.y_px - p0.y_px) ** 2) ** 0.5
        total += seg_len
        distances.append(total)

    if total <= 1e-9:
        mid_x = (sx + tx) / 2.0
        mid_y = (sy + ty) / 2.0
        return tuple(
            LayoutPoint(x_px=point.x_px + mid_x, y_px=point.y_px + mid_y)
            for point in points
        )

    translated: list[LayoutPoint] = []
    for point, distance in zip(points, distances):
        ratio = distance / total
        dx = (sx * (1.0 - ratio)) + (tx * ratio)
        dy = (sy * (1.0 - ratio)) + (ty * ratio)
        translated.append(LayoutPoint(x_px=point.x_px + dx, y_px=point.y_px + dy))
    return tuple(translated)


def _orthogonalize_points(points: tuple[LayoutPoint, ...]) -> tuple[LayoutPoint, ...]:
    if len(points) < 2:
        return points
    orthogonal: list[LayoutPoint] = [points[0]]
    for point in points[1:]:
        prev = orthogonal[-1]
        dx = point.x_px - prev.x_px
        dy = point.y_px - prev.y_px
        if abs(dx) > 1e-6 and abs(dy) > 1e-6:
            bend = LayoutPoint(x_px=point.x_px, y_px=prev.y_px)
            if abs(bend.x_px - prev.x_px) > 1e-6 or abs(bend.y_px - prev.y_px) > 1e-6:
                orthogonal.append(bend)
        orthogonal.append(point)
    deduped: list[LayoutPoint] = []
    for point in orthogonal:
        if (
            deduped
            and abs(deduped[-1].x_px - point.x_px) < 1e-6
            and abs(deduped[-1].y_px - point.y_px) < 1e-6
        ):
            continue
        deduped.append(point)
    return tuple(deduped)
