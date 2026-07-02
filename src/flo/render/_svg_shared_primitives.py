"""Shared SVG primitives used across direct SVG renderers."""

from __future__ import annotations

from html import escape
from typing import Any

from ._svg_sppm_edges import _edge_svg
from ._svg_sppm_nodes import _node_svg
from .layout_core.models import LayoutBounds
from .options import RenderOptions


def standard_svg_defs() -> list[str]:
    """Return the shared arrow marker definitions for direct SVG renderers."""
    return [
        "<defs>",
        '<marker id="flo-sppm-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L8,3 L0,6 z" fill="#475569" />',
        "</marker>",
        "</defs>",
    ]


def standard_lane_svg(lane: Any) -> list[str]:
    """Render a lane frame using the shared direct-SVG style."""
    return [
        f'<g data-lane-id="{escape(str(lane.id))}">',
        f'<rect x="{lane.bounds.x_px:.1f}" y="{lane.bounds.y_px:.1f}" width="{lane.bounds.width_px:.1f}" height="{lane.bounds.height_px:.1f}" rx="18" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />',
        f'<text x="{lane.bounds.x_px + 16.0:.1f}" y="{lane.bounds.y_px + 24.0:.1f}" font-family="Helvetica" font-size="13" font-weight="700" fill="#334155">{escape(str(lane.label))}</text>',
        "</g>",
    ]


def standard_node_svg(
    *,
    node: Any,
    raw_node: dict[str, Any],
    options: RenderOptions,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    """Render one node using the shared SPPM-developed node primitive."""
    return _node_svg(
        node=node,
        raw_node=raw_node,
        options=options,
        x=x,
        y=y,
        width=width,
        height=height,
    )


def standard_edge_svg(
    *,
    edge_path: Any,
    source_bounds: LayoutBounds | None,
    target_bounds: LayoutBounds | None,
    source_kind: str,
    target_kind: str,
    avoid_bounds: tuple[Any, ...],
    canvas_bounds: LayoutBounds,
    diagnostics: list[Any],
    render_as_rework_style: bool = False,
) -> tuple[list[str], tuple[LayoutBounds, ...]]:
    """Render one edge using the shared SPPM-developed edge primitive."""
    return _edge_svg(
        edge_path,
        source_bounds=source_bounds,
        target_bounds=target_bounds,
        source_kind=source_kind,
        target_kind=target_kind,
        avoid_bounds=avoid_bounds,
        canvas_bounds=canvas_bounds,
        diagnostics=diagnostics,
        render_as_rework_style=render_as_rework_style,
    )


def raw_node_lookup(
    process: dict[str, Any] | Any, *, options: RenderOptions
) -> dict[str, dict[str, Any]]:
    """Return raw node payloads keyed by node id for direct SVG rendering."""
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
