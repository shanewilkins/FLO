"""Shared graph helpers for SPPM rework row inference and edge translation."""

from __future__ import annotations

from typing import Iterable

from .layout_core.models import LayoutPoint


def infer_rework_row_ids(
    *,
    node_ids: set[str],
    edges: Iterable[tuple[str, str, bool, str | None]],
) -> tuple[set[str], set[str]]:
    """Infer mainline/rework row membership from edge-level rework semantics."""
    edge_rows = tuple(edges)
    branch_targets = _collect_rework_variant_node_ids(
        edges=edge_rows,
        node_ids=node_ids,
        variant="branch",
        source=False,
    )
    return_sources = _collect_rework_variant_node_ids(
        edges=edge_rows,
        node_ids=node_ids,
        variant="return",
        source=True,
    )
    if not branch_targets:
        return set(), set()

    adjacency = _non_rework_adjacency(edges=edge_rows, node_ids=node_ids)
    rework_node_ids = _reachable_until_return_sources(
        start_ids=branch_targets,
        return_sources=return_sources,
        adjacency=adjacency,
    )

    if not rework_node_ids:
        return set(), set()
    return node_ids - rework_node_ids, rework_node_ids


def translate_edge_points(
    points: tuple[LayoutPoint, ...],
    *,
    source_shift: tuple[float, float],
    target_shift: tuple[float, float],
) -> tuple[LayoutPoint, ...]:
    """Translate edge geometry with linear interpolation between endpoint shifts."""
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


def _collect_rework_variant_node_ids(
    *,
    edges: Iterable[tuple[str, str, bool, str | None]],
    node_ids: set[str],
    variant: str,
    source: bool,
) -> set[str]:
    results: set[str] = set()
    for source_id, target_id, _is_rework, rework_variant in edges:
        if str(rework_variant or "") != variant:
            continue
        candidate = source_id if source else target_id
        if candidate in node_ids:
            results.add(candidate)
    return results


def _non_rework_adjacency(
    *,
    edges: Iterable[tuple[str, str, bool, str | None]],
    node_ids: set[str],
) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for source_id, target_id, is_rework, _rework_variant in edges:
        if is_rework or source_id not in adjacency or target_id not in node_ids:
            continue
        adjacency[source_id].append(target_id)
    return adjacency


def _reachable_until_return_sources(
    *,
    start_ids: set[str],
    return_sources: set[str],
    adjacency: dict[str, list[str]],
) -> set[str]:
    reachable: set[str] = set()
    frontier = list(start_ids)
    while frontier:
        current = frontier.pop()
        if current in reachable:
            continue
        reachable.add(current)
        if current in return_sources:
            continue
        for next_id in adjacency.get(current, []):
            if next_id not in reachable:
                frontier.append(next_id)
    return reachable
