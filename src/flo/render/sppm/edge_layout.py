"""Deterministic annotation placement policy; no SVG serialization."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from .._diagnostics import RenderDiagnostic
from ..layout_core.models import LayoutBounds, LayoutPoint
from .edge_segments import (
    _candidate_segment_indexes,
    _first_rightward_horizontal_segment_index,
    _longest_segment_index,
)

_LANE_HEADER_AVOID_HEIGHT_PX = 34.0


@dataclass(frozen=True)
class _LabelPlacement:
    x: float
    y: float
    anchor: str = "middle"


def _resolve_edge_label_placement(
    *,
    edge_path: Any,
    points: tuple[LayoutPoint, ...],
    rework_edge: bool,
    rework_variant: str,
    source_kind: str,
    avoid_bounds: tuple[Any, ...],
    label_width: float,
    canvas_bounds: Any | None,
    diagnostics: list[RenderDiagnostic] | None,
) -> _LabelPlacement:
    if rework_edge:
        placement = _rework_label_placement(points, rework_variant=rework_variant)
        return _avoid_bounds_overlap(
            placement,
            box_width=label_width,
            box_height=18.0,
            avoid_bounds=avoid_bounds,
            canvas_bounds=canvas_bounds,
            segment_dx=1,
            segment_dy=0,
            diagnostics=diagnostics,
            diagnostic_context={
                "annotation_kind": "rework_label",
                "edge": "->".join(edge_path.edge),
            },
        )

    label_point = getattr(edge_path, "label_point", None)
    if label_point is not None:
        placement = _clamp_placement_to_canvas(
            _LabelPlacement(x=float(label_point.x_px), y=float(label_point.y_px)),
            box_width=label_width,
            box_height=18.0,
            canvas_bounds=canvas_bounds,
        )
        if not _placement_overlaps_bounds(
            placement, box_width=label_width, box_height=18.0, avoid_bounds=avoid_bounds
        ):
            return placement

    return _label_placement(
        points,
        avoid_near_source=bool(
            edge_path.callout_lines and edge_path.callout_near_source
        ),
        prefer_near_source=source_kind.lower() == "decision",
        avoid_bounds=avoid_bounds,
        box_width=label_width,
        box_height=18.0,
        canvas_bounds=canvas_bounds,
        diagnostics=diagnostics,
        diagnostic_context={
            "annotation_kind": "edge_label",
            "edge": f"{edge_path.edge[0]}->{edge_path.edge[1]}",
        },
    )


def _label_placement(
    points: Any,
    *,
    avoid_near_source: bool = False,
    prefer_near_source: bool = False,
    avoid_bounds: tuple[Any, ...] = (),
    box_width: float = 28.0,
    box_height: float = 18.0,
    canvas_bounds: Any | None = None,
    diagnostics: list[RenderDiagnostic] | None = None,
    diagnostic_context: dict[str, Any] | None = None,
) -> _LabelPlacement:
    preferred_index = (
        _first_rightward_horizontal_segment_index(points)
        if prefer_near_source
        else None
    )
    segment_indexes = _candidate_segment_indexes(
        points,
        avoid_near_source=avoid_near_source,
        prefer_near_source=prefer_near_source,
        preferred_index=preferred_index,
    )
    best_index = _longest_segment_index(points, segment_indexes=segment_indexes)
    if best_index is None:
        best_index = _longest_segment_index(
            points, segment_indexes=range(max(0, len(points) - 1))
        )
    if best_index is None:
        return _LabelPlacement(x=float(points[0].x_px), y=float(points[0].y_px))

    best_start = points[best_index]
    best_end = points[best_index + 1]
    dx = float(best_end.x_px - best_start.x_px)
    dy = float(best_end.y_px - best_start.y_px)
    mid_x = (best_start.x_px + best_end.x_px) / 2.0
    mid_y = (best_start.y_px + best_end.y_px) / 2.0
    if abs(dx) >= abs(dy):
        y_offset = -4.0 if prefer_near_source else -8.0
        placement = _LabelPlacement(x=mid_x, y=mid_y + y_offset)
    else:
        offset = 14.0 if dx >= 0 else -14.0
        anchor = "start" if dx >= 0 else "end"
        placement = _LabelPlacement(x=mid_x + offset, y=mid_y - 2.0, anchor=anchor)
    return _avoid_bounds_overlap(
        placement,
        box_width=box_width,
        box_height=box_height,
        avoid_bounds=avoid_bounds,
        segment_dx=dx,
        segment_dy=dy,
        canvas_bounds=canvas_bounds,
        diagnostics=diagnostics,
        diagnostic_context=diagnostic_context,
    )


def _edge_callout_placement(
    points: Any,
    *,
    near_source: bool,
    has_label: bool,
    rework_edge: bool = False,
    avoid_bounds: tuple[Any, ...] = (),
    box_width: float = 88.0,
    box_height: float = 40.0,
    canvas_bounds: Any | None = None,
    diagnostics: list[RenderDiagnostic] | None = None,
    diagnostic_context: dict[str, Any] | None = None,
) -> _LabelPlacement:
    segment_index = _callout_segment_index(
        points,
        near_source=near_source,
    )
    point_index = segment_index + 1
    source = points[point_index - 1]
    target = points[point_index]
    mid_x = (source.x_px + target.x_px) / 2.0
    mid_y = (source.y_px + target.y_px) / 2.0
    dx = float(target.x_px - source.x_px)
    dy = float(target.y_px - source.y_px)
    if abs(dx) >= abs(dy):
        vertical_offset = 34.0 if has_label else 22.0
        placement = _LabelPlacement(x=mid_x, y=mid_y - vertical_offset)
    else:
        offset = 18.0 if dx >= 0 else -18.0
        if rework_edge:
            # Keep rework metadata callouts off the line body.
            offset = (box_width / 2.0) + 22.0
        anchor = "start" if dx >= 0 else "end"
        y_offset = -16.0 if has_label else -10.0
        placement = _LabelPlacement(x=mid_x + offset, y=mid_y + y_offset, anchor=anchor)
    return _avoid_bounds_overlap(
        placement,
        box_width=box_width,
        box_height=box_height,
        avoid_bounds=avoid_bounds,
        segment_dx=dx,
        segment_dy=dy,
        canvas_bounds=canvas_bounds,
        diagnostics=diagnostics,
        diagnostic_context=diagnostic_context,
    )


def _callout_segment_index(points: Any, *, near_source: bool) -> int:
    segment_count = max(0, len(points) - 1)
    if segment_count <= 1:
        return 0
    if near_source:
        return 0

    if segment_count > 2:
        interior_indexes = range(1, segment_count - 1)
        best_index = _longest_segment_index(points, segment_indexes=interior_indexes)
        if best_index is not None:
            return best_index

    best_index = _longest_segment_index(points, segment_indexes=range(segment_count))
    return best_index if best_index is not None else max(0, segment_count - 1)


def _avoid_bounds_overlap(
    placement: _LabelPlacement,
    *,
    box_width: float,
    box_height: float,
    avoid_bounds: tuple[Any, ...],
    segment_dx: float,
    segment_dy: float,
    canvas_bounds: Any | None,
    diagnostics: list[RenderDiagnostic] | None = None,
    diagnostic_context: dict[str, Any] | None = None,
) -> _LabelPlacement:
    offsets = (
        0.0,
        *(offset for step in range(1, 8) for offset in (-28.0 * step, 28.0 * step)),
    )
    horizontal = abs(segment_dx) >= abs(segment_dy)
    candidates = [(0.0, offset) if horizontal else (offset, 0.0) for offset in offsets]
    # A crowded corridor may have no clear position along either single axis.
    # Search a bounded neighborhood in both axes before reporting a fallback.
    candidates.extend(
        sorted(
            ((dx, dy) for dx in offsets[1:] for dy in offsets[1:]),
            key=lambda delta: (abs(delta[0]) + abs(delta[1]), delta),
        )
    )
    for dx, dy in candidates:
        candidate = _clamp_placement_to_canvas(
            _LabelPlacement(placement.x + dx, placement.y + dy, placement.anchor),
            box_width=box_width,
            box_height=box_height,
            canvas_bounds=canvas_bounds,
        )
        if not _placement_overlaps_bounds(
            candidate,
            box_width=box_width,
            box_height=box_height,
            avoid_bounds=avoid_bounds,
        ):
            return candidate
    final_candidate = _clamp_placement_to_canvas(
        placement,
        box_width=box_width,
        box_height=box_height,
        canvas_bounds=canvas_bounds,
    )
    _record_overlap_fallback_diagnostic(
        placement=final_candidate,
        box_width=box_width,
        box_height=box_height,
        avoid_bounds=avoid_bounds,
        diagnostics=diagnostics,
        diagnostic_context=diagnostic_context,
    )
    return final_candidate


def _record_overlap_fallback_diagnostic(
    *,
    placement: _LabelPlacement,
    box_width: float,
    box_height: float,
    avoid_bounds: tuple[Any, ...],
    diagnostics: list[RenderDiagnostic] | None,
    diagnostic_context: dict[str, Any] | None,
) -> None:
    if diagnostics is None:
        return
    if not _placement_overlaps_bounds(
        placement,
        box_width=box_width,
        box_height=box_height,
        avoid_bounds=avoid_bounds,
    ):
        return
    metadata = dict(diagnostic_context or {})
    metadata.update(
        {
            "x": round(placement.x, 2),
            "y": round(placement.y, 2),
            "box_width": round(box_width, 2),
            "box_height": round(box_height, 2),
            "avoid_bounds_count": len(avoid_bounds),
        }
    )
    diagnostics.append(
        RenderDiagnostic(
            code="sppm-annotation-overlap-fallback",
            severity="warning",
            message=(
                "SPPM annotation placement fell back to a placement that still overlaps existing bounds."
            ),
            metadata=metadata,
        )
    )


def _clamp_placement_to_canvas(
    placement: _LabelPlacement,
    *,
    box_width: float,
    box_height: float,
    canvas_bounds: Any | None,
) -> _LabelPlacement:
    if canvas_bounds is None:
        return placement

    min_x = float(canvas_bounds.x_px) + (box_width / 2.0)
    max_x = float(canvas_bounds.x_px + canvas_bounds.width_px) - (box_width / 2.0)
    min_y = float(canvas_bounds.y_px) + 12.0
    max_y = float(canvas_bounds.y_px + canvas_bounds.height_px) - (box_height - 12.0)
    clamped_x = min(max(placement.x, min_x), max_x)
    clamped_y = min(max(placement.y, min_y), max_y)
    return _LabelPlacement(x=clamped_x, y=clamped_y, anchor=placement.anchor)


def _lane_header_avoid_bounds(lanes: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(
        type(lane.bounds)(
            x_px=float(lane.bounds.x_px),
            y_px=float(lane.bounds.y_px),
            width_px=float(lane.bounds.width_px),
            height_px=min(
                float(lane.bounds.height_px),
                _LANE_HEADER_AVOID_HEIGHT_PX,
            ),
        )
        for lane in lanes
    )


def _placement_overlaps_bounds(
    placement: _LabelPlacement,
    *,
    box_width: float,
    box_height: float,
    avoid_bounds: tuple[Any, ...],
) -> bool:
    left = placement.x - (box_width / 2.0)
    right = placement.x + (box_width / 2.0)
    top = placement.y - 12.0
    bottom = top + box_height
    for bounds in avoid_bounds:
        if right <= float(bounds.x_px) or left >= float(bounds.x_px + bounds.width_px):
            continue
        if bottom <= float(bounds.y_px) or top >= float(bounds.y_px + bounds.height_px):
            continue
        return True
    return False


def _annotation_bounds_for_placement(
    placement: _LabelPlacement,
    *,
    box_width: float,
    box_height: float,
) -> LayoutBounds:
    return LayoutBounds(
        x_px=placement.x - (box_width / 2.0),
        y_px=placement.y - 12.0,
        width_px=box_width,
        height_px=box_height,
    )


def _edge_token_placement(points: Any, *, near_source: bool) -> _LabelPlacement:
    point_index = 1 if near_source and len(points) > 1 else max(1, len(points) - 1)
    anchor = points[0] if near_source else points[-1]
    other = points[point_index] if near_source else points[point_index - 1]
    dx = float(other.x_px - anchor.x_px)
    dy = float(other.y_px - anchor.y_px)
    x_offset = 18.0 if dx >= 0 else -18.0
    if abs(dx) >= abs(dy):
        return _LabelPlacement(x=anchor.x_px + x_offset, y=anchor.y_px - 16.0)
    horizontal = 18.0 if dx >= 0 else -18.0
    vertical = -12.0 if dy >= 0 else 12.0
    return _LabelPlacement(x=anchor.x_px + horizontal, y=anchor.y_px + vertical)


def _rework_label_placement(
    points: tuple[LayoutPoint, ...], *, rework_variant: str
) -> _LabelPlacement:
    first = next(iter(points), None)
    if first is None:
        return _LabelPlacement(x=0.0, y=0.0)
    if len(points) < 2:
        return _LabelPlacement(x=float(first.x_px), y=float(first.y_px))
    if rework_variant == "return" and len(points) > 2:
        horizontal_indexes = [
            index
            for index, (segment_start, segment_end) in enumerate(pairwise(points))
            if abs(segment_end.x_px - segment_start.x_px)
            >= abs(segment_end.y_px - segment_start.y_px)
            and abs(segment_end.x_px - segment_start.x_px) > 1e-6
        ]
        segment_index = _longest_segment_index(
            points,
            segment_indexes=horizontal_indexes or range(len(points) - 1),
        )
        if segment_index is not None:
            segment_start = points[segment_index]
            segment_end = points[segment_index + 1]
            if abs(segment_end.x_px - segment_start.x_px) < 1e-6:
                return _LabelPlacement(
                    x=segment_start.x_px + 12.0,
                    y=(segment_start.y_px + segment_end.y_px) / 2.0,
                    anchor="start",
                )
            return _LabelPlacement(
                x=(segment_start.x_px + segment_end.x_px) / 2.0,
                y=segment_start.y_px - 8.0,
            )
    source = points[0]
    target = points[1] if rework_variant == "branch" else points[-1]
    dx = float(target.x_px - source.x_px)
    dy = float(target.y_px - source.y_px)
    if abs(dx) >= abs(dy):
        ratio = 0.14 if rework_variant == "branch" else 0.5
        return _LabelPlacement(
            x=source.x_px + (dx * ratio),
            y=source.y_px + (dy * ratio) - 1.0,
        )
    ratio = 0.14 if rework_variant == "branch" else 0.5
    return _LabelPlacement(
        x=source.x_px + (dx * ratio),
        y=source.y_px + (dy * ratio),
    )
