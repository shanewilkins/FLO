"""Deterministic packing and alignment for the renderer-agnostic placement core."""

from __future__ import annotations

from .models import (
    LinePlacement,
    NodeMeasure,
    OrientationMode,
    PlacementConstraints,
    PlacementPlan,
)


def build_placement_plan(
    nodes: list[NodeMeasure],
    edges: list[tuple[str, str]],
    constraints: PlacementConstraints,
) -> PlacementPlan:
    """Pack nodes into lines and compute full placement geometry.

    Args:
        nodes: Ordered sequence of node measures to pack.
        edges: All logical edges as (source_id, target_id) pairs.
        constraints: Packing and alignment policy.

    Returns:
        A fully resolved PlacementPlan with per-node offsets.

    """
    if not nodes:
        return PlacementPlan(
            lines=(),
            node_line_index={},
            boundary_edges=frozenset(),
            total_major=constraints.margin * 2,
            total_cross=constraints.margin * 2,
            orientation=constraints.orientation,
        )

    groups = _group_into_lines(nodes, constraints)
    raw_lines = _compute_raw_lines(groups, constraints)
    final_lines = _apply_alignment(raw_lines, constraints)

    node_line_index: dict[str, int] = {}
    for line in final_lines:
        for node_id in line.node_ids:
            node_line_index[node_id] = line.line_index

    boundary_edges = _derive_boundary_edges(edges, node_line_index)

    max_major_size = max(r.major_size for r in raw_lines)
    total_major = constraints.margin + max_major_size + constraints.margin

    last_raw = raw_lines[-1]
    total_cross = last_raw.cross_offset + last_raw.cross_size + constraints.margin

    return PlacementPlan(
        lines=tuple(final_lines),
        node_line_index=node_line_index,
        boundary_edges=boundary_edges,
        total_major=total_major,
        total_cross=total_cross,
        orientation=constraints.orientation,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _major_dim(node: NodeMeasure, orientation: OrientationMode) -> int:
    return node.width_px if orientation == "lr" else node.height_px


def _cross_dim(node: NodeMeasure, orientation: OrientationMode) -> int:
    return node.height_px if orientation == "lr" else node.width_px


def _max_major_limit(constraints: PlacementConstraints) -> int | None:
    if constraints.orientation == "lr":
        return constraints.max_width_px
    return constraints.max_height_px


def _line_content_major(
    group: list[NodeMeasure],
    orientation: OrientationMode,
    gap_major: int,
) -> int:
    total = sum(_major_dim(n, orientation) for n in group)
    return total + gap_major * (len(group) - 1)


def _group_into_lines(
    nodes: list[NodeMeasure],
    constraints: PlacementConstraints,
) -> list[list[NodeMeasure]]:
    max_major = _max_major_limit(constraints)
    orientation = constraints.orientation
    gap = constraints.gap_major

    if max_major is None:
        return [list(nodes)]

    groups: list[list[NodeMeasure]] = []
    current: list[NodeMeasure] = []

    for node in nodes:
        dim = _major_dim(node, orientation)
        if not current:
            current.append(node)
            continue
        content = _line_content_major(current, orientation, gap)
        if content + gap + dim > max_major:
            groups.append(current)
            current = [node]
        else:
            current.append(node)

    if current:
        groups.append(current)

    return groups


class _RawLine:
    """Intermediate line geometry computed before alignment shifts are applied."""

    def __init__(
        self,
        line_index: int,
        nodes: list[NodeMeasure],
        orientation: OrientationMode,
        gap_major: int,
        margin: int,
        cross_offset: int,
    ) -> None:
        """Build a raw line geometry from a group of packed nodes."""
        self.line_index = line_index
        self.nodes = nodes
        self.orientation = orientation
        self.gap_major = gap_major
        self.margin = margin
        self.cross_offset = cross_offset

        self.cross_size = max(_cross_dim(n, orientation) for n in nodes)
        self.major_size = _line_content_major(nodes, orientation, gap_major)

        # Per-node major offsets: start at margin (align_stack applied later).
        offsets: list[int] = []
        pos = margin
        for n in nodes:
            offsets.append(pos)
            pos += _major_dim(n, orientation) + gap_major
        self.node_major_offsets = offsets


def _compute_raw_lines(
    groups: list[list[NodeMeasure]],
    constraints: PlacementConstraints,
) -> list[_RawLine]:
    raw: list[_RawLine] = []
    cross_pos = constraints.margin
    for idx, group in enumerate(groups):
        line = _RawLine(
            line_index=idx,
            nodes=group,
            orientation=constraints.orientation,
            gap_major=constraints.gap_major,
            margin=constraints.margin,
            cross_offset=cross_pos,
        )
        raw.append(line)
        cross_pos += line.cross_size + constraints.gap_minor
    return raw


def _apply_alignment(
    raw_lines: list[_RawLine],
    constraints: PlacementConstraints,
) -> list[LinePlacement]:
    orientation = constraints.orientation
    max_major = max(r.major_size for r in raw_lines)
    result: list[LinePlacement] = []

    for raw in raw_lines:
        # align_stack: shift major start for shorter lines.
        stack_shift = _stack_shift(raw.major_size, max_major, constraints.align_stack)
        major_offsets = tuple(o + stack_shift for o in raw.node_major_offsets)

        # align_line: shift individual nodes on cross axis within the line.
        cross_offsets = tuple(
            raw.cross_offset
            + _line_cross_shift(
                node_cross=_cross_dim(n, orientation),
                line_cross=raw.cross_size,
                align=constraints.align_line,
            )
            for n in raw.nodes
        )

        result.append(
            LinePlacement(
                line_index=raw.line_index,
                node_ids=tuple(n.id for n in raw.nodes),
                node_major_offsets=major_offsets,
                node_cross_offsets=cross_offsets,
                major_size=raw.major_size,
                cross_offset=raw.cross_offset,
                cross_size=raw.cross_size,
            )
        )

    return result


def _stack_shift(line_major: int, max_major: int, align: str) -> int:
    delta = max_major - line_major
    if align == "center":
        return delta // 2
    if align == "end":
        return delta
    return 0


def _line_cross_shift(node_cross: int, line_cross: int, align: str) -> int:
    delta = line_cross - node_cross
    if align == "center":
        return delta // 2
    if align == "end":
        return delta
    return 0


def _derive_boundary_edges(
    edges: list[tuple[str, str]],
    node_line_index: dict[str, int],
) -> frozenset[tuple[str, str]]:
    boundary: set[tuple[str, str]] = set()
    for source, target in edges:
        src_line = node_line_index.get(source)
        tgt_line = node_line_index.get(target)
        if src_line is None or tgt_line is None:
            continue
        if src_line != tgt_line:
            boundary.add((source, target))
    return frozenset(boundary)
