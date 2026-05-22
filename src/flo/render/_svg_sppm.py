"""Minimal direct-SVG SPPM renderer backed by ELK layout."""

from __future__ import annotations

from dataclasses import dataclass, replace
from html import escape
from typing import Any

from ._artifact import RenderArtifact
from ._sppm_node_appearance import resolve_sppm_node_appearance
from ._sppm_node_content import build_sppm_node_content
from ._sppm_task_card import build_sppm_task_card_layout
from .layout_core import build_sppm_elk_layout_request, execute_elk_layout
from .layout_core.elk_runtime import run_elkjs_layout
from .layout_core.models import LayoutBounds, LayoutPoint
from .options import RenderOptions
from flo.schema.render_metadata import PROCESS_METADATA_PROCESS_NAME_KEY

_PADDING = 28.0
_LANE_HEADER_AVOID_HEIGHT_PX = 34.0
_SPPM_SYNTHETIC_ROW_PREFIX = "__sppm_row_"


@dataclass(frozen=True)
class _LabelPlacement:
    x: float
    y: float
    anchor: str = "middle"


def render_sppm_svg_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render a minimal standalone SVG for SPPM diagrams using ELK layout."""
    request = build_sppm_elk_layout_request(process, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    display_node_bounds, display_edge_paths = _enforce_sppm_row_alignment(
        node_bounds=result.node_bounds,
        edge_paths=result.edge_paths,
        lanes=result.lanes,
    )
    display_canvas_bounds = _display_canvas_bounds(
        base_canvas=result.canvas_bounds,
        node_bounds=display_node_bounds,
        edge_paths=display_edge_paths,
    )
    raw_node_by_id = _raw_node_lookup(process, options=options)
    title = _process_title(process)

    width = max(1.0, display_canvas_bounds.width_px + (_PADDING * 2.0))
    height = max(
        1.0,
        display_canvas_bounds.height_px + (_PADDING * 2.0) + (36.0 if title else 0.0),
    )
    content_top = _PADDING + (36.0 if title else 0.0)

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg" '
            'data-flo-diagram="sppm">'
        ),
        "<defs>",
        '<marker id="flo-sppm-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L8,3 L0,6 z" fill="#475569" />',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="#fffdf8" />',
    ]

    if title:
        parts.append(
            f'<text x="{_PADDING:.1f}" y="{_PADDING + 4.0:.1f}" font-family="Helvetica" font-size="22" font-weight="700" fill="#0f172a">{escape(title)}</text>'
        )

    parts.append(f'<g transform="translate({_PADDING:.1f},{content_top:.1f})">')

    visible_lanes = tuple(
        lane for lane in result.lanes if not _is_synthetic_sppm_lane(lane.id)
    )
    for lane in visible_lanes:
        parts.extend(_lane_svg(lane))

    avoid_bounds = tuple(display_node_bounds.values()) + _lane_header_avoid_bounds(
        visible_lanes
    )
    canvas_bounds = display_canvas_bounds
    node_kind_by_id = {
        str(node.id): str(node.kind or "task").lower() for node in request.nodes
    }
    occupied_annotation_bounds: list[LayoutBounds] = []
    for edge_key in sorted(display_edge_paths.keys()):
        source_id, target_id = edge_key
        edge_parts, annotation_bounds = _edge_svg(
            display_edge_paths[edge_key],
            source_bounds=display_node_bounds.get(source_id),
            target_bounds=display_node_bounds.get(target_id),
            source_kind=node_kind_by_id.get(source_id, "task"),
            target_kind=node_kind_by_id.get(target_id, "task"),
            avoid_bounds=avoid_bounds + tuple(occupied_annotation_bounds),
            canvas_bounds=canvas_bounds,
        )
        parts.extend(edge_parts)
        occupied_annotation_bounds.extend(annotation_bounds)

    for node in request.nodes:
        bounds = display_node_bounds.get(node.id)
        if bounds is None:
            continue
        raw_node = raw_node_by_id.get(node.id, {})
        parts.extend(
            _node_svg(
                node=node,
                raw_node=raw_node,
                options=options,
                x=bounds.x_px,
                y=bounds.y_px,
                width=bounds.width_px,
                height=bounds.height_px,
            )
        )

    parts.append("</g>")
    parts.append("</svg>")
    return RenderArtifact(kind="svg", content="\n".join(parts), backend="svg"), None


def _raw_node_lookup(
    process: dict[str, Any] | Any, *, options: RenderOptions
) -> dict[str, dict[str, Any]]:
    from .layout_core.elk_support import (
        extract_nodes_and_edges,
        project_parent_only_subprocess_view,
    )

    nodes, edges = extract_nodes_and_edges(process)
    if options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)
    return {
        str(node.get("id") or ""): node for node in nodes if str(node.get("id") or "")
    }


def _process_title(process: dict[str, Any] | Any) -> str | None:
    if isinstance(process, dict):
        process_block = process.get("process")
        if isinstance(process_block, dict):
            title = str(process_block.get("name") or "").strip()
            if title:
                return title
        title = str(process.get("name") or "").strip()
        return title or None

    process_name = getattr(process, "process_name", None)
    if process_name is not None:
        title = str(process_name).strip()
        if title:
            return title

    metadata = getattr(process, "process_metadata", None)
    if isinstance(metadata, dict):
        display_name = str(
            metadata.get(PROCESS_METADATA_PROCESS_NAME_KEY) or ""
        ).strip()
        if display_name:
            return display_name
        title = str(metadata.get("name") or "").strip()
        if title:
            return title

    name = getattr(process, "name", None)
    if name is not None:
        title = str(name).strip()
        if title:
            return title
    return None


def _lane_svg(lane: Any) -> list[str]:
    return [
        f'<g data-lane-id="{escape(lane.id)}">',
        f'<rect x="{lane.bounds.x_px:.1f}" y="{lane.bounds.y_px:.1f}" width="{lane.bounds.width_px:.1f}" height="{lane.bounds.height_px:.1f}" rx="18" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />',
        f'<text x="{lane.bounds.x_px + 16.0:.1f}" y="{lane.bounds.y_px + 24.0:.1f}" font-family="Helvetica" font-size="13" font-weight="700" fill="#334155">{escape(lane.label)}</text>',
        "</g>",
    ]


def _enforce_sppm_row_alignment(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], Any],
    lanes: tuple[Any, ...],
) -> tuple[dict[str, LayoutBounds], dict[tuple[str, str], Any]]:
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

    if not mainline_ids or not rework_ids:
        orthogonal_edges = {
            edge_key: replace(edge_path, points=_orthogonalize_points(edge_path.points))
            for edge_key, edge_path in edge_paths.items()
        }
        return dict(node_bounds), orthogonal_edges

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

    # Keep rework loops below the mainline but distribute their x positions by
    # branch anchor so nodes do not collapse into one vertical stack.
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

    visited_rework_ids: set[str] = set()
    rework_spacing = max(
        220.0,
        max(node_bounds[node_id].width_px for node_id in rework_ids) + 56.0,
    )
    for source_id, target_id in sorted(
        branch_pairs,
        key=lambda pair: (
            node_bounds[pair[0]].x_px + (node_bounds[pair[0]].width_px / 2.0)
        ),
    ):
        if target_id in visited_rework_ids:
            continue
        cluster: set[str] = set()
        stack = [target_id]
        while stack:
            current = stack.pop()
            if current in cluster:
                continue
            cluster.add(current)
            for neighbor in rework_adjacency.get(current, set()):
                if neighbor not in cluster:
                    stack.append(neighbor)
        if not cluster:
            continue

        ordered_cluster: list[str] = [target_id]
        while True:
            current = ordered_cluster[-1]
            next_ids = sorted(
                (
                    node_id
                    for node_id in rework_adjacency.get(current, set())
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
    if start_id is not None and stop_id is not None:
        start_bounds = node_bounds[start_id]
        stop_bounds = node_bounds[stop_id]
        min_center_x = start_bounds.x_px + (start_bounds.width_px / 2.0)
        max_center_x = stop_bounds.x_px + (stop_bounds.width_px / 2.0)
        if min_center_x <= max_center_x:
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

    transformed_nodes: dict[str, LayoutBounds] = {}
    for node_id, bounds in node_bounds.items():
        dx, dy = shifts.get(node_id, (0.0, 0.0))
        transformed_nodes[node_id] = LayoutBounds(
            x_px=bounds.x_px + dx,
            y_px=bounds.y_px + dy,
            width_px=bounds.width_px,
            height_px=bounds.height_px,
        )

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

    return transformed_nodes, transformed_edges


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


def _clamp_value(value: float, *, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        return value
    return min(max(value, minimum), maximum)


def _node_svg(
    *,
    node: Any,
    raw_node: dict[str, Any],
    options: RenderOptions,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    kind = str(node.kind or "task").lower()
    content = build_sppm_node_content(
        node_id=str(node.id),
        kind=kind,
        name=str(node.label or node.id),
        metadata=raw_node.get("metadata") or {},
        workers=raw_node.get("workers") or [],
        note=str(raw_node.get("note") or ""),
        options=options,
    )
    appearance = resolve_sppm_node_appearance(
        kind=kind,
        metadata=raw_node.get("metadata") or {},
        options=options,
    )
    parts = [f'<g data-node-id="{escape(node.id)}" data-node-kind="{escape(kind)}">']
    title_lines = tuple(line for line in str(content.title).split("\n") if line)
    info_lines = content.info_lines
    task_card = (
        build_sppm_task_card_layout(content)
        if kind not in {"decision", "queue", "subprocess", "start", "end"}
        else None
    )

    if kind == "decision":
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)
        parts.append(
            f'<polygon points="{cx:.1f},{y:.1f} {x + width:.1f},{cy:.1f} {cx:.1f},{y + height:.1f} {x:.1f},{cy:.1f}" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2" />'
        )
        label_start_y = cy - ((_line_count(title_lines) - 1) * 8.0) + 5.0
    elif kind == "queue":
        cx = x + (width / 2.0)
        parts.append(
            f'<polygon points="{x:.1f},{y + height:.1f} {x + width:.1f},{y + height:.1f} {cx:.1f},{y:.1f}" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2" />'
        )
        label_start_y = y + height - 28.0 - ((_line_count(title_lines) - 1) * 7.0)
    elif kind == "subprocess":
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)
        rx = width / 2.0
        ry = height / 2.0
        dash_attr = (
            f' stroke-dasharray="{appearance.stroke_dasharray}"'
            if appearance.stroke_dasharray
            else ""
        )
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2"{dash_attr} />'
        )
        label_start_y = y + 24.0
    elif kind in {"start", "end"}:
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="18" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2" />'
        )
        label_start_y = (
            y + (height / 2.0) - ((_line_count(title_lines) - 1) * 8.0) + 5.0
        )
    else:
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="12" fill="white" stroke="{appearance.border}" stroke-width="2" />'
        )
        header_height = max(28.0, 18.0 + (_line_count(title_lines) * 16.0))
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{header_height:.1f}" rx="12" fill="{appearance.fill}" stroke="none" />'
        )
        if info_lines:
            parts.append(
                f'<line x1="{x:.1f}" y1="{y + header_height:.1f}" x2="{x + width:.1f}" y2="{y + header_height:.1f}" stroke="{appearance.border}" stroke-width="1" opacity="0.35" />'
            )
            if task_card is not None:
                left_rail_x = x + task_card.gutter_width_px
                right_rail_x = x + width - task_card.gutter_width_px
                body_top = y + header_height
                body_bottom = y + height
                parts.append(
                    f'<line data-node-port-rail="in" x1="{left_rail_x:.1f}" y1="{body_top:.1f}" x2="{left_rail_x:.1f}" y2="{body_bottom:.1f}" stroke="{appearance.border}" stroke-width="0.8" opacity="0.20" />'
                )
                parts.append(
                    f'<line data-node-port-rail="out" x1="{right_rail_x:.1f}" y1="{body_top:.1f}" x2="{right_rail_x:.1f}" y2="{body_bottom:.1f}" stroke="{appearance.border}" stroke-width="0.8" opacity="0.20" />'
                )
        label_start_y = y + 18.0

    parts.extend(
        _text_lines_svg(
            x=x + (width / 2.0),
            y=label_start_y,
            lines=title_lines,
            size_px=14,
            weight="600",
            fill=appearance.title_fill,
            line_gap_px=16.0,
            anchor="middle",
        )
    )
    if kind == "queue" and info_lines:
        parts.extend(
            _text_lines_svg(
                x=x + (width / 2.0),
                y=label_start_y + (_line_count(title_lines) * 14.0) + 8.0,
                lines=info_lines,
                size_px=11,
                weight="400",
                fill=appearance.info_fill,
                line_gap_px=13.0,
                anchor="middle",
            )
        )
    elif kind == "subprocess" and info_lines:
        parts.extend(
            _text_lines_svg(
                x=x + (width / 2.0),
                y=label_start_y + (_line_count(title_lines) * 15.0) + 6.0,
                lines=info_lines,
                size_px=11,
                weight="400",
                fill=appearance.info_fill,
                line_gap_px=13.0,
                anchor="middle",
            )
        )
    elif info_lines and kind not in {"decision", "start", "end"}:
        body_text_x = x + 12.0
        if task_card is not None:
            body_text_x = (
                x
                + task_card.gutter_width_px
                + task_card.body_padding_px
                + task_card.body_text_offset_px
            )
        parts.extend(
            _text_lines_svg(
                x=body_text_x,
                y=y + max(28.0, 18.0 + (_line_count(title_lines) * 16.0)) + 18.0,
                lines=info_lines,
                size_px=11,
                weight="400",
                fill=appearance.info_fill,
                line_gap_px=13.0,
                anchor="start",
            )
        )
    parts.append("</g>")
    return parts


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


def _text_lines_svg(
    *,
    x: float,
    y: float,
    lines: tuple[str, ...],
    size_px: int,
    weight: str,
    fill: str,
    line_gap_px: float,
    anchor: str,
) -> list[str]:
    if not lines:
        return []
    parts: list[str] = []
    current_y = y
    for line in lines:
        for subline in [segment for segment in line.split("\n") if segment]:
            parts.append(
                f'<text x="{x:.1f}" y="{current_y:.1f}" text-anchor="{anchor}" font-family="Helvetica" font-size="{size_px}" font-weight="{weight}" fill="{fill}">{escape(subline)}</text>'
            )
            current_y += line_gap_px
    return parts


def _line_count(lines: tuple[str, ...]) -> int:
    count = 0
    for line in lines:
        count += len([segment for segment in line.split("\n") if segment])
    return count or 1
