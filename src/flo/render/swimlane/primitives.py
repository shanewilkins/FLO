"""Swimlane-owned SVG presentation primitives."""

from __future__ import annotations

from html import escape
from typing import Any

from .._diagnostics import RenderDiagnostic
from ..layout_core.models import LayoutBounds
from ..options import RenderOptions


def svg_defs(options: RenderOptions) -> list[str]:
    """Return swimlane-specific marker definitions."""
    color = options.resolved_theme.role("connector").border
    return [
        "<defs>",
        '<marker id="flo-swimlane-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        f'<path d="M0,0 L8,3 L0,6 z" fill="{color}" />',
        "</marker>",
        "</defs>",
    ]


def lane_svg(lane: Any, options: RenderOptions) -> list[str]:
    """Render one responsibility lane frame."""
    role = options.resolved_theme.role("lane")
    return [
        f'<g data-lane-id="{escape(str(lane.id), quote=True)}">',
        f'<rect x="{lane.bounds.x_px:.1f}" y="{lane.bounds.y_px:.1f}" width="{lane.bounds.width_px:.1f}" height="{lane.bounds.height_px:.1f}" rx="18" fill="{role.fill}" stroke="{role.border}" stroke-width="1.5" />',
        f'<text x="{lane.bounds.x_px + 8.0:.1f}" y="{lane.bounds.y_px - 6.0:.1f}" font-family="Helvetica" font-size="12" font-weight="700" fill="{role.title_text}">{escape(str(lane.label))}</text>',
        "</g>",
    ]


def node_svg(
    *,
    node: Any,
    raw_node: dict[str, Any],
    options: RenderOptions,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    """Render one swimlane process node without SPPM presentation imports."""
    kind = str(node.kind or "task").lower()
    label = str(node.label or node.id)
    role = _node_role(kind, raw_node=raw_node, options=options)
    parts = [
        f'<g data-node-id="{escape(str(node.id), quote=True)}" data-node-kind="{escape(kind, quote=True)}">',
        *_node_shape(
            kind=kind,
            x=x,
            y=y,
            width=width,
            height=height,
            fill=role.fill,
            border=role.border,
        ),
        f'<text x="{x + width / 2.0:.1f}" y="{y + height / 2.0 + 5.0:.1f}" text-anchor="middle" font-family="Helvetica" font-size="12" font-weight="600" fill="{role.title_text}">{escape(label)}</text>',
        "</g>",
    ]
    return parts


def edge_svg(
    *,
    edge_path: Any,
    options: RenderOptions,
    diagnostics: list[RenderDiagnostic] | None = None,
    **_unused: Any,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    """Render one routed swimlane transition from normalized layout geometry."""
    del diagnostics
    points = tuple(edge_path.points)
    if len(points) < 2:
        return [], ()
    rework = bool(edge_path.is_rework)
    role = options.resolved_theme.role("nva" if rework else "connector")
    polyline = " ".join(f"{point.x_px:.1f},{point.y_px:.1f}" for point in points)
    dash = ' stroke-dasharray="7 5"' if rework else ""
    parts = [
        f'<g data-edge-source="{escape(str(edge_path.edge[0]), quote=True)}" data-edge-target="{escape(str(edge_path.edge[1]), quote=True)}" data-edge-kind="{"rework" if rework else "direct"}">',
        f'<polyline points="{polyline}" fill="none" stroke="{role.border}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#flo-swimlane-arrow)"{dash} />',
    ]
    if edge_path.label:
        label_x, label_y = _edge_label_point(edge_path, points=points)
        parts.append(
            f'<text x="{label_x:.1f}" y="{label_y - 5.0:.1f}" text-anchor="middle" font-family="Helvetica" font-size="11" fill="{role.detail_text}">{escape(str(edge_path.label))}</text>'
        )
    parts.append("</g>")
    return parts, ()


def raw_node_lookup(
    process: dict[str, Any] | Any, *, options: RenderOptions
) -> dict[str, dict[str, Any]]:
    """Return raw renderer-visible nodes keyed by stable identifier."""
    from ..layout_core.elk_support import (
        extract_nodes_and_edges,
        project_parent_only_subprocess_view,
    )

    nodes, edges = extract_nodes_and_edges(process)
    if options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)
    return {
        str(node.get("id") or ""): node for node in nodes if str(node.get("id") or "")
    }


def _node_role(kind: str, *, raw_node: dict[str, Any], options: RenderOptions) -> Any:
    if kind in {"start", "end"}:
        return options.resolved_theme.role("start_end")
    if kind == "decision":
        return options.resolved_theme.role("decision")
    if kind == "queue":
        return options.resolved_theme.role("queue")
    if kind == "subprocess":
        return options.resolved_theme.role("subprocess")
    metadata = raw_node.get("metadata")
    value_class = (
        str(metadata.get("value_class") or "").strip().lower()
        if isinstance(metadata, dict)
        else ""
    )
    return options.resolved_theme.role(
        value_class if value_class in {"va", "rnva", "nva"} else "surface"
    )


def _node_shape(
    *,
    kind: str,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    border: str,
) -> list[str]:
    if kind == "decision":
        cx = x + width / 2.0
        cy = y + height / 2.0
        return [
            f'<polygon points="{cx:.1f},{y:.1f} {x + width:.1f},{cy:.1f} {cx:.1f},{y + height:.1f} {x:.1f},{cy:.1f}" fill="{fill}" stroke="{border}" stroke-width="1.5" />'
        ]
    if kind == "queue":
        return [
            f'<polygon points="{x:.1f},{y:.1f} {x + width:.1f},{y:.1f} {x + width / 2.0:.1f},{y + height:.1f}" fill="{fill}" stroke="{border}" stroke-width="1.5" />'
        ]
    radius = height / 2.0 if kind in {"start", "end"} else 6.0
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="{radius:.1f}" fill="{fill}" stroke="{border}" stroke-width="1.5" />'
    ]
    if kind == "subprocess":
        parts.append(
            f'<rect x="{x + 5.0:.1f}" y="{y + 5.0:.1f}" width="{width - 10.0:.1f}" height="{height - 10.0:.1f}" rx="4" fill="none" stroke="{border}" stroke-width="1" />'
        )
    return parts


def _edge_label_point(
    edge_path: Any, *, points: tuple[Any, ...]
) -> tuple[float, float]:
    label_point = getattr(edge_path, "label_point", None)
    if label_point is not None:
        return float(label_point.x_px), float(label_point.y_px)
    middle = points[len(points) // 2]
    return float(middle.x_px), float(middle.y_px)
