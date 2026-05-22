"""Edge, label, and clipping helpers for direct SPPM SVG rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from ._svg_sppm_nodes import _text_lines_svg
from .layout_core.models import LayoutBounds, LayoutPoint

_LANE_HEADER_AVOID_HEIGHT_PX = 34.0
_SPPM_SYNTHETIC_ROW_PREFIX = "__sppm_row_"


@dataclass(frozen=True)
class _LabelPlacement:
    x: float
    y: float
    anchor: str = "middle"


def _edge_svg(
    edge_path: Any,
    *,
    source_bounds: LayoutBounds | None = None,
    target_bounds: LayoutBounds | None = None,
    source_kind: str = "task",
    target_kind: str = "task",
    avoid_bounds: tuple[Any, ...] = (),
    canvas_bounds: Any | None = None,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    points = _prefer_vertical_branch_drop(
        edge_path.points,
        rework_variant=str(edge_path.rework_variant or ""),
        source_bounds=source_bounds,
        target_bounds=target_bounds,
    )
    points = _clip_edge_points_to_node_bounds(
        points,
        source_bounds=source_bounds,
        source_kind=source_kind,
        target_bounds=target_bounds,
        target_kind=target_kind,
    )
    points = _normalize_rework_edge_points(
        points,
        is_rework=bool(edge_path.is_rework),
        rework_variant=str(edge_path.rework_variant or ""),
    )
    if len(points) < 2:
        return [], ()
    polyline = " ".join(f"{point.x_px:.1f},{point.y_px:.1f}" for point in points)
    edge_kind = "rework" if bool(edge_path.is_rework) else "direct"
    rework_variant = str(edge_path.rework_variant or "")
    stroke, dash_pattern, stroke_width = _edge_stroke(edge_path)
    dash_attrs = f' stroke-dasharray="{dash_pattern}"' if dash_pattern else ""
    annotation_bounds: list[LayoutBounds] = []
    parts = [
        f'<g data-edge-source="{escape(edge_path.edge[0])}" data-edge-target="{escape(edge_path.edge[1])}" data-edge-kind="{edge_kind}"{_edge_variant_attr(rework_variant)}>',
        (
            f'<polyline points="{polyline}" fill="none" stroke="{stroke}" '
            f'stroke-width="{stroke_width:.1f}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#flo-sppm-arrow)"{dash_attrs} />'
        ),
    ]
    if edge_path.label:
        label_width = max(28.0, float(len(edge_path.label) * 7.0))
        placement = _label_placement(
            points,
            avoid_near_source=bool(
                edge_path.callout_lines and edge_path.callout_near_source
            ),
            avoid_bounds=avoid_bounds,
            box_width=label_width,
            box_height=18.0,
            canvas_bounds=canvas_bounds,
        )
        label_text = escape(edge_path.label)
        parts.append(
            f'<rect x="{placement.x - (label_width / 2.0):.1f}" y="{placement.y - 12.0:.1f}" width="{label_width:.1f}" height="18.0" rx="7" fill="#fffdf8" fill-opacity="0.95" />'
        )
        parts.append(
            f'<text x="{placement.x:.1f}" y="{placement.y + 1.0:.1f}" text-anchor="{placement.anchor}" font-family="Helvetica" font-size="12" fill="#0f172a">{label_text}</text>'
        )
        annotation_bounds.append(
            _annotation_bounds_for_placement(
                placement,
                box_width=label_width,
                box_height=18.0,
            )
        )
    if edge_path.callout_lines:
        callout_parts, callout_bounds = _edge_callout_svg(
            points=points,
            lines=edge_path.callout_lines,
            near_source=bool(edge_path.callout_near_source),
            has_label=bool(edge_path.label),
            avoid_bounds=avoid_bounds + tuple(annotation_bounds),
            canvas_bounds=canvas_bounds,
        )
        parts.extend(callout_parts)
        annotation_bounds.extend(callout_bounds)
    if edge_path.outgoing_token:
        parts.extend(
            _edge_token_svg(
                points=points,
                token=str(edge_path.outgoing_token),
                near_source=True,
            )
        )
    if edge_path.incoming_token:
        parts.extend(
            _edge_token_svg(
                points=points,
                token=str(edge_path.incoming_token),
                near_source=False,
            )
        )
    parts.append("</g>")
    return parts, tuple(annotation_bounds)


def _label_placement(
    points: Any,
    *,
    avoid_near_source: bool = False,
    avoid_bounds: tuple[Any, ...] = (),
    box_width: float = 28.0,
    box_height: float = 18.0,
    canvas_bounds: Any | None = None,
) -> _LabelPlacement:
    segment_indexes = _candidate_segment_indexes(
        points,
        avoid_near_source=avoid_near_source,
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
        placement = _LabelPlacement(x=mid_x, y=mid_y - 8.0)
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
    )


def _candidate_segment_indexes(points: Any, *, avoid_near_source: bool) -> range:
    segment_count = max(0, len(points) - 1)
    if not avoid_near_source or segment_count <= 2:
        return range(segment_count)
    return range(2, segment_count)


def _longest_segment_index(points: Any, *, segment_indexes: Any) -> int | None:
    best_index: int | None = None
    best_length = -1.0
    for index in segment_indexes:
        start = points[index]
        end = points[index + 1]
        dx = float(end.x_px - start.x_px)
        dy = float(end.y_px - start.y_px)
        length = abs(dx) + abs(dy)
        if length <= best_length:
            continue
        best_length = length
        best_index = index
    return best_index


def _edge_callout_svg(
    *,
    points: Any,
    lines: tuple[str, ...],
    near_source: bool,
    has_label: bool,
    avoid_bounds: tuple[Any, ...] = (),
    canvas_bounds: Any | None = None,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    max_chars = max(len(line) for line in lines)
    width = max(88.0, float(max_chars * 6.7) + 18.0)
    height = 12.0 + (len(lines) * 14.0)
    placement = _edge_callout_placement(
        points,
        near_source=near_source,
        has_label=has_label,
        avoid_bounds=avoid_bounds,
        box_width=width,
        box_height=height,
        canvas_bounds=canvas_bounds,
    )
    x = placement.x - (width / 2.0)
    y = placement.y - 12.0
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="7" fill="#ffffff" stroke="#666666" stroke-width="1" fill-opacity="0.96" />'
    ]
    parts.extend(
        _text_lines_svg(
            x=placement.x,
            y=y + 15.0,
            lines=lines,
            size_px=10,
            weight="400",
            fill="#0f172a",
            line_gap_px=14.0,
            anchor="middle",
        )
    )
    return parts, (
        _annotation_bounds_for_placement(
            placement,
            box_width=width,
            box_height=height,
        ),
    )


def _edge_callout_placement(
    points: Any,
    *,
    near_source: bool,
    has_label: bool,
    avoid_bounds: tuple[Any, ...] = (),
    box_width: float = 88.0,
    box_height: float = 40.0,
    canvas_bounds: Any | None = None,
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
) -> _LabelPlacement:
    if not avoid_bounds:
        return _clamp_placement_to_canvas(
            placement,
            box_width=box_width,
            box_height=box_height,
            canvas_bounds=canvas_bounds,
        )

    if abs(segment_dx) >= abs(segment_dy):
        candidate_offsets = (0.0, -28.0, 28.0, -56.0, 56.0, -84.0, 84.0)
        for offset in candidate_offsets:
            candidate = _LabelPlacement(
                x=placement.x,
                y=placement.y + offset,
                anchor=placement.anchor,
            )
            candidate = _clamp_placement_to_canvas(
                candidate,
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
        return _clamp_placement_to_canvas(
            placement,
            box_width=box_width,
            box_height=box_height,
            canvas_bounds=canvas_bounds,
        )

    candidate_offsets = (0.0, -28.0, 28.0, -56.0, 56.0, -84.0, 84.0)
    for offset in candidate_offsets:
        candidate = _LabelPlacement(
            x=placement.x + offset,
            y=placement.y,
            anchor=placement.anchor,
        )
        candidate = _clamp_placement_to_canvas(
            candidate,
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
    return _clamp_placement_to_canvas(
        placement,
        box_width=box_width,
        box_height=box_height,
        canvas_bounds=canvas_bounds,
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


def _edge_token_svg(*, points: Any, token: str, near_source: bool) -> list[str]:
    placement = _edge_token_placement(points, near_source=near_source)
    token_width = max(42.0, float(len(token) * 7.2) + 16.0)
    x = placement.x - (token_width / 2.0)
    y = placement.y - 11.0
    return [
        f'<g data-edge-token="{escape(token)}" data-edge-token-position="{"source" if near_source else "target"}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{token_width:.1f}" height="22.0" rx="11" fill="#ffffff" stroke="#455A64" stroke-width="1.2" />',
        f'<text x="{placement.x:.1f}" y="{placement.y + 3.0:.1f}" text-anchor="middle" font-family="Helvetica" font-size="9" font-weight="600" fill="#455A64">{escape(token)}</text>',
        "</g>",
    ]


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


def _edge_stroke(edge_path: Any) -> tuple[str, str | None, float]:
    if not bool(edge_path.is_rework):
        return "#475569", None, 2.5
    variant = str(edge_path.rework_variant or "")
    if variant == "branch":
        return "#b91c1c", "8 6", 2.6
    if variant == "return":
        return "#c2410c", "4 6", 2.4
    return "#b91c1c", "8 6", 2.5


def _edge_variant_attr(rework_variant: str) -> str:
    if not rework_variant:
        return ""
    return f' data-edge-rework-variant="{escape(rework_variant)}"'


def _prefer_vertical_branch_drop(
    points: tuple[LayoutPoint, ...],
    *,
    rework_variant: str,
    source_bounds: LayoutBounds | None,
    target_bounds: LayoutBounds | None,
) -> tuple[LayoutPoint, ...]:
    if rework_variant != "branch":
        return points
    if source_bounds is None or target_bounds is None:
        return points
    source_center_x = source_bounds.x_px + (source_bounds.width_px / 2.0)
    source_center_y = source_bounds.y_px + (source_bounds.height_px / 2.0)
    target_center_y = target_bounds.y_px + (target_bounds.height_px / 2.0)
    if target_center_y <= source_center_y:
        return points
    return (
        LayoutPoint(x_px=source_center_x, y_px=source_center_y),
        LayoutPoint(x_px=source_center_x, y_px=target_center_y),
    )


def _normalize_rework_edge_points(
    points: tuple[LayoutPoint, ...], *, is_rework: bool, rework_variant: str
) -> tuple[LayoutPoint, ...]:
    if not is_rework or len(points) < 2:
        return points

    start = points[0]
    end = points[-1]
    if abs(start.x_px - end.x_px) < 1e-6 or abs(start.y_px - end.y_px) < 1e-6:
        return (start, end)

    if rework_variant == "return":
        return _dedupe_points(
            (
                start,
                LayoutPoint(x_px=end.x_px, y_px=start.y_px),
                end,
            )
        )

    if rework_variant == "branch":
        elbow_y = (start.y_px + end.y_px) / 2.0
        return _dedupe_points(
            (
                start,
                LayoutPoint(x_px=start.x_px, y_px=elbow_y),
                LayoutPoint(x_px=end.x_px, y_px=elbow_y),
                end,
            )
        )

    return points


def _dedupe_points(points: tuple[LayoutPoint, ...]) -> tuple[LayoutPoint, ...]:
    deduped: list[LayoutPoint] = []
    for point in points:
        if (
            deduped
            and abs(deduped[-1].x_px - point.x_px) < 1e-6
            and abs(deduped[-1].y_px - point.y_px) < 1e-6
        ):
            continue
        deduped.append(point)
    return tuple(deduped)


def _is_synthetic_sppm_lane(lane_id: str) -> bool:
    return str(lane_id).startswith(_SPPM_SYNTHETIC_ROW_PREFIX)


def _clip_edge_points_to_node_bounds(
    points: tuple[LayoutPoint, ...],
    *,
    source_bounds: LayoutBounds | None,
    source_kind: str,
    target_bounds: LayoutBounds | None,
    target_kind: str,
) -> tuple[LayoutPoint, ...]:
    if len(points) < 2:
        return points

    clipped_points = list(points)
    if source_bounds is not None:
        clipped_points[0] = _shape_edge_point(
            bounds=source_bounds,
            kind=source_kind,
            toward=clipped_points[1],
        )
    if target_bounds is not None:
        clipped_points[-1] = _shape_edge_point(
            bounds=target_bounds,
            kind=target_kind,
            toward=clipped_points[-2],
        )
    return tuple(clipped_points)


def _shape_edge_point(
    *, bounds: LayoutBounds, kind: str, toward: LayoutPoint
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    dx = float(toward.x_px - cx)
    dy = float(toward.y_px - cy)
    if dx == 0.0 and dy == 0.0:
        return LayoutPoint(x_px=cx, y_px=cy)

    normalized_kind = str(kind or "task").lower()
    if normalized_kind == "decision":
        return _diamond_edge_point(bounds=bounds, dx=dx, dy=dy)
    if normalized_kind == "subprocess":
        return _ellipse_edge_point(bounds=bounds, dx=dx, dy=dy)
    if normalized_kind == "queue":
        return _queue_triangle_edge_point(bounds=bounds, dx=dx, dy=dy)
    return _rect_edge_point(bounds=bounds, dx=dx, dy=dy)


def _rect_edge_point(*, bounds: LayoutBounds, dx: float, dy: float) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    half_w = max(0.5, float(bounds.width_px) / 2.0)
    half_h = max(0.5, float(bounds.height_px) / 2.0)
    tx = float("inf") if dx == 0.0 else abs(half_w / dx)
    ty = float("inf") if dy == 0.0 else abs(half_h / dy)
    t = min(tx, ty)
    return LayoutPoint(x_px=cx + (dx * t), y_px=cy + (dy * t))


def _diamond_edge_point(*, bounds: LayoutBounds, dx: float, dy: float) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    half_w = max(0.5, float(bounds.width_px) / 2.0)
    half_h = max(0.5, float(bounds.height_px) / 2.0)
    scale = (abs(dx) / half_w) + (abs(dy) / half_h)
    if scale <= 0.0:
        return LayoutPoint(x_px=cx, y_px=cy)
    t = 1.0 / scale
    return LayoutPoint(x_px=cx + (dx * t), y_px=cy + (dy * t))


def _ellipse_edge_point(*, bounds: LayoutBounds, dx: float, dy: float) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    rx = max(0.5, float(bounds.width_px) / 2.0)
    ry = max(0.5, float(bounds.height_px) / 2.0)
    denom = ((dx * dx) / (rx * rx)) + ((dy * dy) / (ry * ry))
    if denom <= 0.0:
        return LayoutPoint(x_px=cx, y_px=cy)
    t = 1.0 / (denom**0.5)
    return LayoutPoint(x_px=cx + (dx * t), y_px=cy + (dy * t))


def _queue_triangle_edge_point(
    *, bounds: LayoutBounds, dx: float, dy: float
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    triangle = (
        LayoutPoint(
            x_px=float(bounds.x_px), y_px=float(bounds.y_px + bounds.height_px)
        ),
        LayoutPoint(
            x_px=float(bounds.x_px + bounds.width_px),
            y_px=float(bounds.y_px + bounds.height_px),
        ),
        LayoutPoint(
            x_px=float(bounds.x_px + (bounds.width_px / 2.0)), y_px=float(bounds.y_px)
        ),
    )

    intersections: list[tuple[float, LayoutPoint]] = []
    for start, end in (
        (triangle[0], triangle[1]),
        (triangle[1], triangle[2]),
        (triangle[2], triangle[0]),
    ):
        hit = _ray_segment_intersection(
            origin=LayoutPoint(x_px=cx, y_px=cy),
            direction=LayoutPoint(x_px=dx, y_px=dy),
            segment_start=start,
            segment_end=end,
        )
        if hit is None:
            continue
        intersections.append(hit)

    if not intersections:
        return _rect_edge_point(bounds=bounds, dx=dx, dy=dy)
    _, point = min(intersections, key=lambda item: item[0])
    return point


def _ray_segment_intersection(
    *,
    origin: LayoutPoint,
    direction: LayoutPoint,
    segment_start: LayoutPoint,
    segment_end: LayoutPoint,
) -> tuple[float, LayoutPoint] | None:
    px = float(origin.x_px)
    py = float(origin.y_px)
    rx = float(direction.x_px)
    ry = float(direction.y_px)
    qx = float(segment_start.x_px)
    qy = float(segment_start.y_px)
    sx = float(segment_end.x_px - segment_start.x_px)
    sy = float(segment_end.y_px - segment_start.y_px)

    rxs = (rx * sy) - (ry * sx)
    if abs(rxs) < 1e-9:
        return None

    qmpx = qx - px
    qmpy = qy - py
    t = ((qmpx * sy) - (qmpy * sx)) / rxs
    u = ((qmpx * ry) - (qmpy * rx)) / rxs
    if t < 0.0 or u < 0.0 or u > 1.0:
        return None
    return (
        t,
        LayoutPoint(x_px=px + (t * rx), y_px=py + (t * ry)),
    )
