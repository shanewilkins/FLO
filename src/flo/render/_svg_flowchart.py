"""Minimal direct-SVG flowchart renderer backed by ELK layout."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from ._artifact import RenderArtifact
from .layout_core import build_flowchart_elk_layout_request, execute_elk_layout
from .layout_core.elk_runtime import run_elkjs_layout
from .options import RenderOptions

_PADDING = 24.0


@dataclass(frozen=True)
class _LabelPlacement:
    x: float
    y: float
    anchor: str = "middle"


def render_flowchart_svg_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render a minimal standalone SVG for flowcharts using ELK layout."""
    request = build_flowchart_elk_layout_request(process, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    node_by_id = {node.id: node for node in request.nodes}

    width = max(1.0, result.canvas_bounds.width_px + (_PADDING * 2.0))
    height = max(1.0, result.canvas_bounds.height_px + (_PADDING * 2.0))

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg" '
            'data-flo-diagram="flowchart">'
        ),
        "<defs>",
        '<marker id="flo-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L8,3 L0,6 z" fill="#334155" />',
        "</marker>",
        "</defs>",
        '<rect width="100%" height="100%" fill="white" />',
        f'<g transform="translate({_PADDING:.1f},{_PADDING:.1f})">',
    ]

    for edge_key in sorted(result.edge_paths.keys()):
        edge_path = result.edge_paths[edge_key]
        parts.extend(_edge_svg(edge_path))

    for node_id in [node.id for node in request.nodes]:
        bounds = result.bounds_for(node_id)
        if bounds is None:
            continue
        node = node_by_id.get(node_id)
        if node is None:
            continue
        parts.extend(
            _node_svg(
                node=node,
                x=bounds.x_px,
                y=bounds.y_px,
                width=bounds.width_px,
                height=bounds.height_px,
            )
        )

    parts.append("</g>")
    parts.append("</svg>")
    return RenderArtifact(kind="svg", content="\n".join(parts), backend="svg"), None


def _node_svg(
    *, node: Any, x: float, y: float, width: float, height: float
) -> list[str]:
    label = escape(str(node.label or node.id))
    kind = str(node.kind or "task").lower()
    fill, stroke = _node_colors(kind)
    parts = [f'<g data-node-id="{escape(node.id)}" data-node-kind="{escape(kind)}">']
    if kind == "decision":
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)
        parts.append(
            f'<polygon points="{cx:.1f},{y:.1f} {x + width:.1f},{cy:.1f} {cx:.1f},{y + height:.1f} {x:.1f},{cy:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    elif kind in {"start", "end"}:
        parts.append(
            f'<ellipse cx="{x + (width / 2.0):.1f}" cy="{y + (height / 2.0):.1f}" '
            f'rx="{width / 2.0:.1f}" ry="{height / 2.0:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    else:
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
            f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    parts.append(
        f'<text x="{x + (width / 2.0):.1f}" y="{y + (height / 2.0) + 5.0:.1f}" text-anchor="middle" font-family="Helvetica" font-size="14">{label}</text>'
    )
    parts.append("</g>")
    return parts


def _edge_svg(edge_path: Any) -> list[str]:
    points = edge_path.points
    if len(points) < 2:
        return []
    polyline = " ".join(f"{point.x_px:.1f},{point.y_px:.1f}" for point in points)
    parts = [
        f'<g data-edge-source="{escape(edge_path.edge[0])}" data-edge-target="{escape(edge_path.edge[1])}">',
        (
            f'<polyline points="{polyline}" fill="none" stroke="#334155" '
            'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#flo-arrow)" />'
        ),
    ]
    if edge_path.label:
        placement = _label_placement(points)
        parts.append(
            f'<rect x="{placement.x - 12.0:.1f}" y="{placement.y - 12.0:.1f}" width="24.0" height="16.0" rx="6" fill="white" fill-opacity="0.92" />'
        )
        parts.append(
            f'<text x="{placement.x:.1f}" y="{placement.y:.1f}" text-anchor="{placement.anchor}" font-family="Helvetica" font-size="12" fill="#0f172a">{escape(edge_path.label)}</text>'
        )
    parts.append("</g>")
    return parts


def _label_placement(points: Any) -> _LabelPlacement:
    best_start = points[0]
    best_end = points[-1]
    best_length = -1.0

    for start, end in zip(points, points[1:]):
        dx = float(end.x_px - start.x_px)
        dy = float(end.y_px - start.y_px)
        length = abs(dx) + abs(dy)
        if length <= best_length:
            continue
        best_length = length
        best_start = start
        best_end = end

    mid_x = (best_start.x_px + best_end.x_px) / 2.0
    mid_y = (best_start.y_px + best_end.y_px) / 2.0
    dx = float(best_end.x_px - best_start.x_px)
    dy = float(best_end.y_px - best_start.y_px)

    if abs(dx) >= abs(dy):
        return _LabelPlacement(x=mid_x, y=mid_y - 8.0)
    offset = 10.0 if dx >= 0 else -10.0
    anchor = "start" if dx >= 0 else "end"
    return _LabelPlacement(x=mid_x + offset, y=mid_y - 2.0, anchor=anchor)


def _node_colors(kind: str) -> tuple[str, str]:
    if kind == "start":
        return "#dcfce7", "#166534"
    if kind == "end":
        return "#fee2e2", "#991b1b"
    if kind == "decision":
        return "#fef3c7", "#92400e"
    return "#eff6ff", "#1d4ed8"
