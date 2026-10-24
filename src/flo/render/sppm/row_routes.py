"""Bounded orthogonal routes between nodes after horizontal row alignment."""

from __future__ import annotations

from typing import Any

from ..layout_core.models import LayoutBounds, LayoutPoint


def _rebuild_forward_route(edge_path, source_bounds, target_bounds):
    if source_bounds is None or target_bounds is None:
        return None
    if edge_path.source_port_side != "EAST" or edge_path.target_port_side != "WEST":
        return None
    source = _bounds_anchor(source_bounds, "EAST")
    target = _bounds_anchor(target_bounds, "WEST")
    if source.x_px >= target.x_px:
        return None
    if abs(source.y_px - target.y_px) < 1e-6:
        return (source, target)
    corridor_x = (source.x_px + target.x_px) / 2
    return (
        source,
        LayoutPoint(x_px=corridor_x, y_px=source.y_px),
        LayoutPoint(x_px=corridor_x, y_px=target.y_px),
        target,
    )


def _rebuild_rework_route(
    *,
    edge_path: Any,
    source_bounds: LayoutBounds | None,
    target_bounds: LayoutBounds | None,
    mainline_bottom: float | None = None,
) -> tuple[LayoutPoint, ...] | None:
    if source_bounds is None or target_bounds is None:
        return None

    if edge_path.rework_variant == "branch" and edge_path.is_rework:
        source = _bounds_anchor(source_bounds, "SOUTH")
        target = _bounds_anchor(target_bounds, "NORTH")
        if abs(source.x_px - target.x_px) < 1e-6:
            return (source, target)
        corridor_y = (source.y_px + target.y_px) / 2.0
        return (
            source,
            LayoutPoint(x_px=source.x_px, y_px=corridor_y),
            LayoutPoint(x_px=target.x_px, y_px=corridor_y),
            target,
        )

    if edge_path.rework_variant == "branch" and not edge_path.is_rework:
        source = _bounds_anchor(source_bounds, "SOUTH")
        target = _bounds_anchor(target_bounds, "WEST")
        turn_y = source.y_px + max(24.0, (target.y_px - source.y_px) / 2.0)
        approach_x = target.x_px - 24.0
        return (
            source,
            LayoutPoint(x_px=source.x_px, y_px=turn_y),
            LayoutPoint(x_px=approach_x, y_px=turn_y),
            LayoutPoint(x_px=approach_x, y_px=target.y_px),
            target,
        )

    if edge_path.rework_variant == "return" and edge_path.is_rework:
        if mainline_bottom is not None:
            source = _bounds_anchor(source_bounds, "WEST")
            target = _bounds_anchor(target_bounds, "SOUTH")
            corridor_y = (mainline_bottom + source_bounds.y_px) / 2
            corridor_x = source.x_px - 24
            return (
                source,
                LayoutPoint(x_px=corridor_x, y_px=source.y_px),
                LayoutPoint(x_px=corridor_x, y_px=corridor_y),
                LayoutPoint(x_px=target.x_px, y_px=corridor_y),
                target,
            )
        source = _bounds_anchor(source_bounds, "NORTH")
        target = _bounds_anchor(target_bounds, "SOUTH")
        source_clearance_y = source.y_px - 24.0
        target_clearance_y = target.y_px + 24.0
        corridor_x = (
            max(
                source_bounds.x_px + source_bounds.width_px,
                target_bounds.x_px + target_bounds.width_px,
            )
            + 28.0
        )
        return (
            source,
            LayoutPoint(x_px=source.x_px, y_px=source_clearance_y),
            LayoutPoint(x_px=corridor_x, y_px=source_clearance_y),
            LayoutPoint(x_px=corridor_x, y_px=target_clearance_y),
            LayoutPoint(x_px=target.x_px, y_px=target_clearance_y),
            target,
        )

    return None


def _bounds_anchor(bounds: LayoutBounds, side: str) -> LayoutPoint:
    center_x = bounds.x_px + (bounds.width_px / 2.0)
    center_y = bounds.y_px + (bounds.height_px / 2.0)
    if side == "NORTH":
        return LayoutPoint(x_px=center_x, y_px=bounds.y_px)
    if side == "SOUTH":
        return LayoutPoint(x_px=center_x, y_px=bounds.y_px + bounds.height_px)
    if side == "WEST":
        return LayoutPoint(x_px=bounds.x_px, y_px=center_y)
    return LayoutPoint(x_px=bounds.x_px + bounds.width_px, y_px=center_y)
