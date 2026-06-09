"""Minimal direct-SVG SPPM renderer backed by ELK layout."""

from __future__ import annotations

from html import escape
from typing import Any

from flo.schema.render_metadata import PROCESS_METADATA_PROCESS_NAME_KEY

from ._artifact import RenderArtifact
from ._diagnostics import (
    build_render_diagnostics_report,
    log_render_diagnostics,
    serialize_render_diagnostics,
    serialize_render_diagnostics_report,
)
from ._svg_sppm_edges import _annotation_bounds_for_placement
from ._svg_sppm_edges import _edge_callout_placement
from ._svg_sppm_edges import _edge_svg
from ._svg_sppm_edges import _is_synthetic_sppm_lane
from ._svg_sppm_edges import _label_placement
from ._svg_sppm_edges import _lane_header_avoid_bounds
from ._svg_sppm_nodes import _node_svg
from ._svg_sppm_rows import _display_canvas_bounds
from ._svg_sppm_rows import _enforce_sppm_row_alignment
from ._svg_sppm_rows import row_gap_diagnostics
from .layout_core import build_sppm_elk_layout_request, execute_elk_layout
from .layout_core.elk_runtime import run_elkjs_layout
from .layout_core.models import LayoutBounds
from .options import RenderOptions

_PADDING = 28.0

__all__ = [
    "render_sppm_svg_artifact",
    "_annotation_bounds_for_placement",
    "_edge_callout_placement",
    "_label_placement",
    "_lane_header_avoid_bounds",
    "row_gap_diagnostics",
]


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
    postprocess_diagnostics = row_gap_diagnostics(
        node_bounds=display_node_bounds,
        lanes=result.lanes,
        edge_paths=display_edge_paths,
    )
    diagnostics = tuple(result.diagnostics) + tuple(postprocess_diagnostics)
    diagnostics_report = build_render_diagnostics_report(
        diagnostics,
        diagram="sppm",
        backend="svg",
        artifact_kind="svg",
        strict=options.layout_fit == "fit-strict",
    )
    log_render_diagnostics(diagnostics_report)
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
            'data-flo-diagram="sppm" data-flo-layout-engine="elk">'
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
    return (
        RenderArtifact(
            kind="svg",
            content="\n".join(parts),
            backend="svg",
            metadata={
                "render_diagnostics": serialize_render_diagnostics(diagnostics),
                "render_diagnostics_report": serialize_render_diagnostics_report(
                    diagnostics_report
                ),
            },
        ),
        None,
    )


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
        return _first_non_empty(
            _clean_text(process.get("process", {}).get("name"))
            if isinstance(process.get("process"), dict)
            else None,
            _clean_text(process.get("name")),
        )

    metadata = getattr(process, "process_metadata", None)
    metadata_name = (
        _first_non_empty(
            _clean_text(metadata.get(PROCESS_METADATA_PROCESS_NAME_KEY)),
            _clean_text(metadata.get("name")),
        )
        if isinstance(metadata, dict)
        else None
    )
    return _first_non_empty(
        _clean_text(getattr(process, "process_name", None)),
        metadata_name,
        _clean_text(getattr(process, "name", None)),
    )


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _lane_svg(lane: Any) -> list[str]:
    return [
        f'<g data-lane-id="{escape(lane.id)}">',
        f'<rect x="{lane.bounds.x_px:.1f}" y="{lane.bounds.y_px:.1f}" width="{lane.bounds.width_px:.1f}" height="{lane.bounds.height_px:.1f}" rx="18" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />',
        f'<text x="{lane.bounds.x_px + 16.0:.1f}" y="{lane.bounds.y_px + 24.0:.1f}" font-family="Helvetica" font-size="13" font-weight="700" fill="#334155">{escape(lane.label)}</text>',
        "</g>",
    ]
