"""Shape attachment and connector normalization policy for SPPM finalization."""

from __future__ import annotations

from .._diagnostics import RenderDiagnostic
from ..layout_core.models import LayoutBounds, LayoutPoint

_ATTACHMENT_MISS_WARN_PX = 24.0


def _normalize_rework_edge_points(
    points: tuple[LayoutPoint, ...], *, is_rework: bool, rework_variant: str
) -> tuple[LayoutPoint, ...]:
    if not is_rework:
        return _dedupe_points(points)
    normalized_variant = str(rework_variant or "")
    if normalized_variant not in {"branch", "return"}:
        return points
    deduped = _dedupe_points(points)
    if len(deduped) < 3:
        return deduped
    start = deduped[0]
    end = deduped[-1]
    aligned_x = all(abs(point.x_px - start.x_px) <= 1e-6 for point in deduped)
    aligned_y = all(abs(point.y_px - start.y_px) <= 1e-6 for point in deduped)
    if aligned_x or aligned_y:
        return (start, end)
    return deduped


def _dedupe_points(points: tuple[LayoutPoint, ...]) -> tuple[LayoutPoint, ...]:
    deduped: list[LayoutPoint] = []
    for point in points:
        if (
            deduped
            and abs(deduped[-1].x_px - point.x_px) < 1e-6
            and abs(deduped[-1].y_px - point.y_px) < 1e-6
        ):
            continue
        if len(deduped) >= 2:
            first, second = deduped[-2:]
            vertical = (
                abs(first.x_px - second.x_px) < 1e-6
                and abs(second.x_px - point.x_px) < 1e-6
                and (second.y_px - first.y_px) * (point.y_px - second.y_px) >= 0
            )
            horizontal = (
                abs(first.y_px - second.y_px) < 1e-6
                and abs(second.y_px - point.y_px) < 1e-6
                and (second.x_px - first.x_px) * (point.x_px - second.x_px) >= 0
            )
            if vertical or horizontal:
                deduped.pop()
        deduped.append(point)
    return tuple(deduped)


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
    if normalized_kind in {"queue", "wait"}:
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
    if normalized_kind in {"queue", "wait"}:
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
        LayoutPoint(x_px=float(bounds.x_px), y_px=float(bounds.y_px)),
        LayoutPoint(x_px=float(bounds.x_px + bounds.width_px), y_px=float(bounds.y_px)),
        LayoutPoint(
            x_px=float(bounds.x_px + (bounds.width_px / 2.0)),
            y_px=float(bounds.y_px + bounds.height_px),
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
