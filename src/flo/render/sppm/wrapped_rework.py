"""Bounded, deterministic placement of simple rework beside frozen wrap rows."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from itertools import pairwise

from ..layout_core.elk_contracts import ElkLayoutLane, ElkLayoutRequest
from ..layout_core.models import LayoutBounds, RoutedEdgePath
from ..layout_core.rework_geometry import boxes_overlap, segment_hits


def simple_rework_chains(
    request: ElkLayoutRequest,
) -> list[tuple[str, str, tuple[str, ...]]]:
    """Accept only isolated linear corrections with one departure and one rejoin."""
    row_by_node = {
        node: lane.id
        for lane in request.lanes
        if not lane.id.startswith("__sppm_row_wrap_rework_")
        for node in lane.node_ids
    }
    rework = {
        node
        for lane in request.lanes
        if lane.id.startswith("__sppm_row_wrap_rework_")
        for node in lane.node_ids
    }
    incoming, outgoing = _rework_connections(request, rework)
    order = {node: index for index, node in enumerate(row_by_node)}
    result = []
    for edge in sorted(
        request.edges,
        key=lambda e: (order.get(e.source_id, len(order)), e.source_id, e.target_id),
    ):
        if edge.rework_variant != "branch" or edge.source_id not in row_by_node:
            continue
        chain = _walk_simple_chain(edge.target_id, incoming, outgoing)
        if chain is not None:
            target, nodes = chain
            if row_by_node.get(target) == row_by_node[edge.source_id]:
                result.append((edge.source_id, target, nodes))
    return result


def _rework_connections(request, rework):
    incoming = {node: [] for node in rework}
    outgoing = {node: [] for node in rework}
    for edge in request.edges:
        if edge.target_id in incoming:
            incoming[edge.target_id].append(edge)
        if edge.source_id in outgoing:
            outgoing[edge.source_id].append(edge)
    return incoming, outgoing


def _walk_simple_chain(start, incoming, outgoing):
    chain = []
    current = start
    while current in outgoing and current not in chain:
        if len(incoming[current]) != 1 or len(outgoing[current]) != 1:
            break
        chain.append(current)
        following = outgoing[current][0]
        if following.rework_variant == "return":
            return following.target_id, tuple(chain)
        if following.is_rework or following.rework_variant is not None:
            break
        current = following.target_id
    return None


def choose_rework_rows(
    request: ElkLayoutRequest,
    score: Callable[[ElkLayoutRequest], tuple[int, int, int, float]],
) -> ElkLayoutRequest:
    """Evaluate two candidates once per chain; never repack mainline rows."""
    for source, _target, chain in simple_rework_chains(request):
        chain_ids = set(chain)
        lanes = tuple(
            replace(
                lane,
                node_ids=tuple(node for node in lane.node_ids if node not in chain_ids),
            )
            for lane in request.lanes
        )
        lanes = tuple(lane for lane in lanes if lane.node_ids)
        anchor = next(
            index for index, lane in enumerate(lanes) if source in lane.node_ids
        )
        local = ElkLayoutLane(
            id=f"__sppm_row_wrap_rework_local_{len(source)}_{source}_{chain[0]}",
            label="",
            node_ids=chain,
        )
        candidates = []
        for above in (False, True):
            index = anchor if above else anchor + 1
            candidate = replace(request, lanes=(*lanes[:index], local, *lanes[index:]))
            candidates.append(((*score(candidate), int(above)), candidate))
        best_score, best_candidate = min(candidates, key=lambda item: item[0])
        if best_score[0] == 0:
            request = best_candidate
    return request


def align_rework_rows(
    request: ElkLayoutRequest, bounds: dict[str, LayoutBounds]
) -> None:
    """Align correction endpoints with their anchors when spacing permits."""
    mainline_right = max(
        (
            b.x_px + b.width_px
            for node, b in bounds.items()
            if any(
                node in lane.node_ids
                and not lane.id.startswith("__sppm_row_wrap_rework_")
                for lane in request.lanes
            )
        ),
        default=12.0,
    )
    for source, target, chain in simple_rework_chains(request):
        if not any(
            lane.id.startswith("__sppm_row_wrap_rework_local_")
            and lane.node_ids == chain
            for lane in request.lanes
        ):
            continue
        _ensure_anchor_clearance(request, source, target, chain, bounds)
        aligned = _anchor_aligned_chain(source, target, chain, bounds)
        if aligned is not None:
            bounds.update(aligned)
            continue
        first, last = bounds[chain[0]], bounds[chain[-1]]
        width = last.x_px + last.width_px - first.x_px
        center = (
            bounds[source].x_px
            + bounds[source].width_px / 2
            + bounds[target].x_px
            + bounds[target].width_px / 2
        ) / 2
        left = max(12.0, min(center - width / 2, mainline_right - width))
        shift = left - first.x_px
        for node in chain:
            bounds[node] = replace(bounds[node], x_px=bounds[node].x_px + shift)


def _ensure_anchor_clearance(request, source, target, chain, bounds):
    if len(chain) < 2:
        return
    start = bounds[source].x_px + bounds[source].width_px / 2
    end = bounds[target].x_px + bounds[target].width_px / 2
    if end <= start:
        return
    required = sum(
        (bounds[a].width_px + bounds[b].width_px) / 2 + 24.0 for a, b in pairwise(chain)
    )
    deficit = required - (end - start)
    if deficit <= 0:
        return
    lane = next(lane for lane in request.lanes if source in lane.node_ids)
    # Reserve horizontal clearance once; preserve all mainline row membership.
    for node in lane.node_ids[lane.node_ids.index(target) :]:
        bounds[node] = replace(bounds[node], x_px=bounds[node].x_px + deficit)


def _anchor_aligned_chain(source, target, chain, bounds):
    if len(chain) < 2:
        return None
    start = bounds[source].x_px + bounds[source].width_px / 2
    end = bounds[target].x_px + bounds[target].width_px / 2
    # Local correction cards may use a compact 24px gap without moving the
    # frozen mainline columns. Final bounds include any rightward extension.
    required = [0.0]
    for previous, current in pairwise(chain):
        required.append(
            required[-1]
            + (bounds[previous].width_px + bounds[current].width_px) / 2
            + 24.0
        )
    slack = end - start - required[-1]
    if slack < 0 or start - bounds[chain[0]].width_px / 2 < 0.0:
        return None
    return {
        node: replace(
            bounds[node],
            x_px=start
            + required[index]
            + slack * index / (len(chain) - 1)
            - bounds[node].width_px / 2,
        )
        for index, node in enumerate(chain)
    }


def route_score(
    bounds: dict[str, LayoutBounds],
    paths: dict[tuple[str, str], RoutedEdgePath],
) -> tuple[int, int, int, float]:
    """Rank collisions, crossings, bends, then Manhattan route length."""
    collisions = crossings = bends = 0
    length = 0.0
    segments = []
    for key, path in sorted(paths.items()):
        points = tuple(
            point
            for i, point in enumerate(path.points)
            if i == 0 or point != path.points[i - 1]
        )
        bends += sum(
            (b.x_px - a.x_px) * (c.y_px - b.y_px)
            != (b.y_px - a.y_px) * (c.x_px - b.x_px)
            for a, b, c in zip(points, points[1:], points[2:], strict=False)
        )
        for a, b in pairwise(points):
            length += abs(b.x_px - a.x_px) + abs(b.y_px - a.y_px)
            collisions += sum(
                segment_hits(a, b, box)
                for node, box in bounds.items()
                if node not in key
            )
            segments.append((key, a, b))
        collisions += _caption_collisions(path, points, bounds)
    for i, (key, a, b) in enumerate(segments):
        for other, c, d in segments[i + 1 :]:
            if key != other:
                crossings += _segments_cross(a, b, c, d)
    return collisions, crossings, bends, length


def _caption_collisions(path, points, bounds) -> int:
    # Fixed envelope: wording and presence cannot change side selection.
    if path.rework_variant not in {"branch", "return"} or len(points) < 2:
        return 0
    a, b = max(
        pairwise(points),
        key=lambda pair: (
            pair[0].y_px == pair[1].y_px,
            abs(pair[1].x_px - pair[0].x_px) + abs(pair[1].y_px - pair[0].y_px),
        ),
    )
    label = LayoutBounds(
        (a.x_px + b.x_px - 240) / 2, (a.y_px + b.y_px) / 2 - 14, 240, 24
    )
    return sum(boxes_overlap(label, box) for box in bounds.values())


def _segments_cross(a, b, c, d) -> bool:
    if a.x_px == b.x_px and c.y_px == d.y_px:
        return min(c.x_px, d.x_px) < a.x_px < max(c.x_px, d.x_px) and min(
            a.y_px, b.y_px
        ) < c.y_px < max(a.y_px, b.y_px)
    if a.y_px == b.y_px and c.x_px == d.x_px:
        return min(a.x_px, b.x_px) < c.x_px < max(a.x_px, b.x_px) and min(
            c.y_px, d.y_px
        ) < a.y_px < max(c.y_px, d.y_px)
    return False
