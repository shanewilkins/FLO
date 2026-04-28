"""Deterministic corridor-lane planning derived from a PlacementPlan.

Phase 3 introduces a renderer-independent corridor skeleton that later routing
stages can consume. This module intentionally does not emit DOT or mutate any
renderer behavior by default.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import PlacementPlan


@dataclass(frozen=True)
class CorridorLane:
    """One corridor lane between two adjacent placement lines."""

    id: str
    line_from: int
    line_to: int
    channel_index: int


@dataclass(frozen=True)
class CorridorAnchor:
    """Deterministic edge-to-corridor anchor metadata."""

    edge: tuple[str, str]
    lane_id: str
    node_id: str
    line_index: int


@dataclass(frozen=True)
class CorridorPlan:
    """Renderer-agnostic corridor skeleton and occupancy metadata."""

    lanes: tuple[CorridorLane, ...]
    entry_anchors: dict[tuple[str, str], CorridorAnchor]
    exit_anchors: dict[tuple[str, str], CorridorAnchor]
    lane_occupancy: dict[str, tuple[tuple[str, str], ...]]
    edge_lane_hops: dict[tuple[str, str], tuple[str, ...]]


def build_corridor_plan(
    *,
    placement: PlacementPlan,
    lane_channels: int = 1,
    edges: list[tuple[str, str]] | None = None,
) -> CorridorPlan:
    """Build a deterministic corridor plan from placement lines.

    Args:
        placement: Placement output that defines line boundaries.
        lane_channels: Number of channels to allocate for each adjacent pair
            of lines. Values less than 1 are normalized to 1.
        edges: Optional logical edges to project through the corridor. When not
            provided, placement.boundary_edges is used.

    Returns:
        CorridorPlan with fixed lanes, anchors, and occupancy metadata.

    """
    channel_count = max(1, lane_channels)
    lanes = _build_lanes(placement=placement, channel_count=channel_count)
    if not lanes:
        return _empty_corridor_plan()

    lane_lookup = {(lane.line_from, lane.line_to, lane.channel_index): lane.id for lane in lanes}
    candidate_edges = sorted(edges if edges is not None else placement.boundary_edges)
    edge_pair_path, pair_edges = _collect_edge_pair_paths(
        candidate_edges=candidate_edges,
        node_line_index=placement.node_line_index,
    )
    pair_assignment, lane_occupancy_lists = _assign_pair_channels(
        pair_edges=pair_edges,
        lane_lookup=lane_lookup,
        lane_ids={lane.id for lane in lanes},
        channel_count=channel_count,
    )
    entry_anchors, exit_anchors, edge_lane_hops = _build_edge_anchor_metadata(
        edge_pair_path=edge_pair_path,
        pair_assignment=pair_assignment,
        lane_lookup=lane_lookup,
        node_line_index=placement.node_line_index,
    )
    lane_occupancy = _freeze_lane_occupancy(lane_occupancy_lists)

    return CorridorPlan(
        lanes=tuple(lanes),
        entry_anchors=entry_anchors,
        exit_anchors=exit_anchors,
        lane_occupancy=lane_occupancy,
        edge_lane_hops=edge_lane_hops,
    )


def _empty_corridor_plan() -> CorridorPlan:
    return CorridorPlan(
        lanes=(),
        entry_anchors={},
        exit_anchors={},
        lane_occupancy={},
        edge_lane_hops={},
    )


def _collect_edge_pair_paths(
    *,
    candidate_edges: list[tuple[str, str]],
    node_line_index: dict[str, int],
) -> tuple[dict[tuple[str, str], tuple[tuple[int, int], ...]], dict[tuple[int, int], list[tuple[str, str]]]]:
    edge_pair_path: dict[tuple[str, str], tuple[tuple[int, int], ...]] = {}
    pair_edges: dict[tuple[int, int], list[tuple[str, str]]] = {}
    for edge in candidate_edges:
        source, target = edge
        src_line = node_line_index.get(source)
        dst_line = node_line_index.get(target)
        if src_line is None or dst_line is None or src_line == dst_line:
            continue
        pair_path = tuple(_adjacent_pairs_in_traversal_order(src_line=src_line, dst_line=dst_line))
        if not pair_path:
            continue
        edge_pair_path[edge] = pair_path
        for pair in pair_path:
            pair_edges.setdefault(pair, []).append(edge)
    return edge_pair_path, pair_edges


def _assign_pair_channels(
    *,
    pair_edges: dict[tuple[int, int], list[tuple[str, str]]],
    lane_lookup: dict[tuple[int, int, int], str],
    lane_ids: set[str],
    channel_count: int,
) -> tuple[dict[tuple[tuple[int, int], tuple[str, str]], int], dict[str, list[tuple[str, str]]]]:
    pair_assignment: dict[tuple[tuple[int, int], tuple[str, str]], int] = {}
    lane_occupancy_lists: dict[str, list[tuple[str, str]]] = {lane_id: [] for lane_id in lane_ids}
    for pair, traversing_edges in sorted(pair_edges.items()):
        for idx, edge in enumerate(sorted(traversing_edges)):
            channel_idx = idx % channel_count
            pair_assignment[(pair, edge)] = channel_idx
            lane_id = lane_lookup[(pair[0], pair[1], channel_idx)]
            lane_occupancy_lists[lane_id].append(edge)
    return pair_assignment, lane_occupancy_lists


def _build_edge_anchor_metadata(
    *,
    edge_pair_path: dict[tuple[str, str], tuple[tuple[int, int], ...]],
    pair_assignment: dict[tuple[tuple[int, int], tuple[str, str]], int],
    lane_lookup: dict[tuple[int, int, int], str],
    node_line_index: dict[str, int],
) -> tuple[
    dict[tuple[str, str], CorridorAnchor],
    dict[tuple[str, str], CorridorAnchor],
    dict[tuple[str, str], tuple[str, ...]],
]:
    entry_anchors: dict[tuple[str, str], CorridorAnchor] = {}
    exit_anchors: dict[tuple[str, str], CorridorAnchor] = {}
    edge_lane_hops: dict[tuple[str, str], tuple[str, ...]] = {}
    for edge, pair_path in sorted(edge_pair_path.items()):
        lane_hops = _lane_hops_for_edge(
            edge=edge,
            pair_path=pair_path,
            pair_assignment=pair_assignment,
            lane_lookup=lane_lookup,
        )
        edge_lane_hops[edge] = tuple(lane_hops)
        source, target = edge
        src_line = node_line_index[source]
        dst_line = node_line_index[target]
        entry_anchors[edge] = CorridorAnchor(
            edge=edge,
            lane_id=lane_hops[0],
            node_id=source,
            line_index=src_line,
        )
        exit_anchors[edge] = CorridorAnchor(
            edge=edge,
            lane_id=lane_hops[-1],
            node_id=target,
            line_index=dst_line,
        )
    return entry_anchors, exit_anchors, edge_lane_hops


def _lane_hops_for_edge(
    *,
    edge: tuple[str, str],
    pair_path: tuple[tuple[int, int], ...],
    pair_assignment: dict[tuple[tuple[int, int], tuple[str, str]], int],
    lane_lookup: dict[tuple[int, int, int], str],
) -> list[str]:
    lane_hops: list[str] = []
    for pair in pair_path:
        channel_idx = pair_assignment[(pair, edge)]
        lane_hops.append(lane_lookup[(pair[0], pair[1], channel_idx)])
    return lane_hops


def _freeze_lane_occupancy(
    lane_occupancy_lists: dict[str, list[tuple[str, str]]],
) -> dict[str, tuple[tuple[str, str], ...]]:
    return {
        lane_id: tuple(lane_occupancy_lists[lane_id])
        for lane_id in sorted(lane_occupancy_lists.keys())
        if lane_occupancy_lists[lane_id]
    }


def _build_lanes(*, placement: PlacementPlan, channel_count: int) -> list[CorridorLane]:
    lanes: list[CorridorLane] = []
    line_count = len(placement.lines)
    if line_count <= 1:
        return lanes

    for line_idx in range(line_count - 1):
        for channel_idx in range(channel_count):
            lanes.append(
                CorridorLane(
                    id=f"corridor_lane_{line_idx}_{channel_idx}",
                    line_from=line_idx,
                    line_to=line_idx + 1,
                    channel_index=channel_idx,
                )
            )
    return lanes


def _adjacent_pairs_in_traversal_order(*, src_line: int, dst_line: int) -> list[tuple[int, int]]:
    if src_line < dst_line:
        return [(line_idx, line_idx + 1) for line_idx in range(src_line, dst_line)]
    if src_line > dst_line:
        return [(line_idx - 1, line_idx) for line_idx in range(src_line, dst_line, -1)]
    return []