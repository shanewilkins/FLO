"""Edge, label, and clipping helpers for direct SPPM SVG rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from ._diagnostics import RenderDiagnostic
from ._svg_sppm_nodes import _text_lines_svg
from ._svg_sppm_edge_segments import (
    _candidate_segment_indexes,
    _first_rightward_horizontal_segment_index,
    _longest_segment_index,
)
from .layout_core.models import LayoutBounds, LayoutPoint

_LANE_HEADER_AVOID_HEIGHT_PX = 34.0
_SPPM_SYNTHETIC_ROW_PREFIX = "__sppm_row_"
_ATTACHMENT_MISS_WARN_PX = 24.0


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
    diagnostics: list[RenderDiagnostic] | None = None,
    render_as_rework_style: bool = False,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    rework_edge = bool(edge_path.is_rework or render_as_rework_style)
    original_points = _normalize_rework_edge_points(
        edge_path.points,
        is_rework=rework_edge,
        rework_variant=str(edge_path.rework_variant or ""),
    )
    points = _clip_edge_points_to_node_bounds(
        original_points,
        source_bounds=source_bounds,
        source_kind=source_kind,
        target_bounds=target_bounds,
        target_kind=target_kind,
        diagnostics=diagnostics,
        edge_id=f"{edge_path.edge[0]}->{edge_path.edge[1]}",
    )
    if len(points) < 2:
        return [], ()
    polyline = " ".join(f"{point.x_px:.1f},{point.y_px:.1f}" for point in points)
    edge_kind = "rework" if rework_edge else "direct"
    rework_variant = str(edge_path.rework_variant or "")
    stroke, dash_pattern, stroke_width = _edge_stroke(
        edge_path,
        render_as_rework_style=render_as_rework_style,
    )
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
        label_point = getattr(edge_path, "label_point", None)
        if rework_edge:
            placement = _rework_label_placement(points, rework_variant=rework_variant)
            placement = _clamp_placement_to_canvas(
                placement,
                box_width=label_width,
                box_height=18.0,
                canvas_bounds=canvas_bounds,
            )
        elif label_point is not None:
            placement = _clamp_placement_to_canvas(
                _LabelPlacement(x=float(label_point.x_px), y=float(label_point.y_px)),
                box_width=label_width,
                box_height=18.0,
                canvas_bounds=canvas_bounds,
            )
        else:
            placement = _label_placement(
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
            rework_edge=rework_edge,
            avoid_bounds=avoid_bounds + tuple(annotation_bounds),
            canvas_bounds=canvas_bounds,
            diagnostics=diagnostics,
            diagnostic_context={
                "annotation_kind": "edge_callout",
                "edge": f"{edge_path.edge[0]}->{edge_path.edge[1]}",
            },
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
    if prefer_near_source:
        return _clamp_placement_to_canvas(
            placement,
            box_width=box_width,
            box_height=box_height,
            canvas_bounds=canvas_bounds,
        )
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


def _edge_callout_svg(
    *,
    points: Any,
    lines: tuple[str, ...],
    near_source: bool,
    has_label: bool,
    rework_edge: bool,
    avoid_bounds: tuple[Any, ...] = (),
    canvas_bounds: Any | None = None,
    diagnostics: list[RenderDiagnostic] | None = None,
    diagnostic_context: dict[str, Any] | None = None,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    max_chars = max(len(line) for line in lines)
    width = max(88.0, float(max_chars * 6.7) + 18.0)
    height = 12.0 + (len(lines) * 14.0)
    placement = _edge_callout_placement(
        points,
        near_source=near_source,
        has_label=has_label,
        rework_edge=rework_edge,
        avoid_bounds=avoid_bounds,
        box_width=width,
        box_height=height,
        canvas_bounds=canvas_bounds,
        diagnostics=diagnostics,
        diagnostic_context=diagnostic_context,
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
    if not avoid_bounds:
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


def _edge_stroke(
    edge_path: Any,
    *,
    render_as_rework_style: bool = False,
) -> tuple[str, str | None, float]:
    if not bool(edge_path.is_rework or render_as_rework_style):
        return "#475569", None, 2.5
    variant = str(edge_path.rework_variant or "")
    if variant == "branch":
        return "#b91c1c", "2 6", 2.6
    if variant == "return":
        return "#c2410c", "2 6", 2.4
    return "#b91c1c", "2 6", 2.5


def _edge_variant_attr(rework_variant: str) -> str:
    if not rework_variant:
        return ""
    return f' data-edge-rework-variant="{escape(rework_variant)}"'


def _has_explicit_attachment_ports(edge_path: Any) -> bool:
    return bool(
        getattr(edge_path, "source_port_side", None)
        and getattr(edge_path, "target_port_side", None)
    )


def _normalize_rework_edge_points(
    points: tuple[LayoutPoint, ...], *, is_rework: bool, rework_variant: str
) -> tuple[LayoutPoint, ...]:
    if not is_rework:
        return points
    normalized_variant = str(rework_variant or "")
    if normalized_variant not in {"branch", "return"}:
        return points
    deduped = _dedupe_points(points)
    if len(deduped) < 3:
        return deduped
    start = deduped[0]
    end = deduped[-1]
    if abs(start.x_px - end.x_px) <= 24.0 or abs(start.y_px - end.y_px) <= 24.0:
        return (start, end)
    return deduped


def _rework_label_placement(
    points: tuple[LayoutPoint, ...], *, rework_variant: str
) -> _LabelPlacement:
    first = next(iter(points), None)
    if first is None:
        return _LabelPlacement(x=0.0, y=0.0)
    if len(points) < 2:
        return _LabelPlacement(x=float(first.x_px), y=float(first.y_px))
    source = points[0]
    target = points[-1]
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
    diagnostics: list[RenderDiagnostic] | None = None,
    edge_id: str | None = None,
) -> tuple[LayoutPoint, ...]:
    if len(points) < 2:
        return points

    clipped_points = list(points)
    if source_bounds is not None:
        original_source = clipped_points[0]
        clipped_points[0] = _shape_edge_point(
            bounds=source_bounds,
            kind=source_kind,
            toward=clipped_points[1],
        )
        _record_attachment_quality_diagnostic(
            diagnostics=diagnostics,
            edge_id=edge_id,
            endpoint_role="source",
            node_kind=source_kind,
            node_bounds=source_bounds,
            original_point=original_source,
            clipped_point=clipped_points[0],
        )
    if target_bounds is not None:
        original_target = clipped_points[-1]
        clipped_points[-1] = _shape_edge_point(
            bounds=target_bounds,
            kind=target_kind,
            toward=clipped_points[-2],
        )
        _record_attachment_quality_diagnostic(
            diagnostics=diagnostics,
            edge_id=edge_id,
            endpoint_role="target",
            node_kind=target_kind,
            node_bounds=target_bounds,
            original_point=original_target,
            clipped_point=clipped_points[-1],
        )
    return tuple(clipped_points)


def _record_attachment_quality_diagnostic(
    *,
    diagnostics: list[RenderDiagnostic] | None,
    edge_id: str | None,
    endpoint_role: str,
    node_kind: str,
    node_bounds: LayoutBounds,
    original_point: LayoutPoint,
    clipped_point: LayoutPoint,
) -> None:
    if diagnostics is None:
        return
    miss_distance_px = _point_distance(original_point, clipped_point)
    allowed_miss_px = _attachment_miss_warn_px(
        node_kind=node_kind,
        node_bounds=node_bounds,
    )
    if miss_distance_px <= allowed_miss_px:
        return
    diagnostics.append(
        RenderDiagnostic(
            code="sppm-attachment-miss-distance",
            severity="warning",
            message=(
                "SPPM endpoint clipping required a large attachment correction from the ELK endpoint."
            ),
            metadata={
                "edge": edge_id,
                "endpoint_role": endpoint_role,
                "node_kind": str(node_kind or "task").lower(),
                "miss_distance_px": round(miss_distance_px, 2),
                "max_expected_miss_px": round(allowed_miss_px, 2),
                "original_x": round(original_point.x_px, 2),
                "original_y": round(original_point.y_px, 2),
                "clipped_x": round(clipped_point.x_px, 2),
                "clipped_y": round(clipped_point.y_px, 2),
            },
        )
    )


def _attachment_miss_warn_px(*, node_kind: str, node_bounds: LayoutBounds) -> float:
    normalized_kind = str(node_kind or "task").lower()
    if normalized_kind == "queue":
        # ELK attaches to the queue's bounding box, while SVG clips to the inset
        # triangle face. The expected horizontal correction is one quarter width.
        return max(_ATTACHMENT_MISS_WARN_PX, float(node_bounds.width_px) / 4.0)
    return _ATTACHMENT_MISS_WARN_PX


def _point_distance(first: LayoutPoint, second: LayoutPoint) -> float:
    dx = float(first.x_px - second.x_px)
    dy = float(first.y_px - second.y_px)
    return (dx * dx + dy * dy) ** 0.5


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
        return _diamond_edge_point(bounds=bounds, dx=dx, dy=dy, cardinalize=True)
    if normalized_kind in {"start", "end"}:
        return _rounded_rect_edge_point(
            bounds=bounds,
            dx=dx,
            dy=dy,
            radius_px=18.0,
            cardinalize=True,
        )
    if normalized_kind == "subprocess":
        return _ellipse_edge_point(bounds=bounds, dx=dx, dy=dy)
    if normalized_kind == "queue":
        return _queue_triangle_edge_point(bounds=bounds, dx=dx, dy=dy, cardinalize=True)
    return _rect_edge_point(bounds=bounds, dx=dx, dy=dy, cardinalize=True)


def _rect_edge_point(
    *, bounds: LayoutBounds, dx: float, dy: float, cardinalize: bool = False
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    if cardinalize:
        dx, dy = _cardinal_direction(dx=dx, dy=dy)
    half_w = max(0.5, float(bounds.width_px) / 2.0)
    half_h = max(0.5, float(bounds.height_px) / 2.0)
    tx = float("inf") if dx == 0.0 else abs(half_w / dx)
    ty = float("inf") if dy == 0.0 else abs(half_h / dy)
    t = min(tx, ty)
    return LayoutPoint(x_px=cx + (dx * t), y_px=cy + (dy * t))


def _diamond_edge_point(
    *, bounds: LayoutBounds, dx: float, dy: float, cardinalize: bool = False
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    if cardinalize:
        dx, dy = _cardinal_direction(dx=dx, dy=dy)
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
    *, bounds: LayoutBounds, dx: float, dy: float, cardinalize: bool = False
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    if cardinalize:
        dx, dy = _cardinal_direction(dx=dx, dy=dy)
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


def _rounded_rect_edge_point(
    *,
    bounds: LayoutBounds,
    dx: float,
    dy: float,
    radius_px: float,
    cardinalize: bool = False,
) -> LayoutPoint:
    cx = float(bounds.x_px + (bounds.width_px / 2.0))
    cy = float(bounds.y_px + (bounds.height_px / 2.0))
    half_w = max(0.5, float(bounds.width_px) / 2.0)
    half_h = max(0.5, float(bounds.height_px) / 2.0)
    corner_radius = max(0.0, min(float(radius_px), half_w, half_h))
    if cardinalize:
        dx, dy = _cardinal_direction(dx=dx, dy=dy)
    if dx == 0.0 and dy == 0.0:
        return LayoutPoint(x_px=cx, y_px=cy)

    axis_eps = 1e-9
    if abs(dx) < axis_eps:
        y = cy + (half_h if dy > 0.0 else -half_h)
        return LayoutPoint(x_px=cx, y_px=y)
    if abs(dy) < axis_eps:
        x = cx + (half_w if dx > 0.0 else -half_w)
        return LayoutPoint(x_px=x, y_px=cy)

    inner_half_w = half_w - corner_radius
    inner_half_h = half_h - corner_radius

    tx = float("inf") if dx == 0.0 else abs(inner_half_w / dx)
    ty = float("inf") if dy == 0.0 else abs(inner_half_h / dy)
    t_inner = min(tx, ty)
    inner_x = cx + (dx * t_inner)
    inner_y = cy + (dy * t_inner)

    corner_cx = cx + (inner_half_w if dx > 0.0 else -inner_half_w)
    corner_cy = cy + (inner_half_h if dy > 0.0 else -inner_half_h)
    radial_x = inner_x - corner_cx
    radial_y = inner_y - corner_cy
    radial_len = (radial_x * radial_x + radial_y * radial_y) ** 0.5
    if radial_len <= axis_eps:
        return LayoutPoint(x_px=inner_x, y_px=inner_y)
    scale = corner_radius / radial_len
    return LayoutPoint(
        x_px=corner_cx + (radial_x * scale),
        y_px=corner_cy + (radial_y * scale),
    )


def _cardinal_direction(*, dx: float, dy: float) -> tuple[float, float]:
    if abs(dx) >= abs(dy):
        return (1.0 if dx >= 0.0 else -1.0), 0.0
    return 0.0, (1.0 if dy >= 0.0 else -1.0)


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
