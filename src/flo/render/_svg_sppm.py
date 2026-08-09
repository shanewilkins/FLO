"""Minimal direct-SVG SPPM renderer backed by ELK layout."""

from __future__ import annotations

from html import escape
from typing import Any

from flo.services.errors import RenderError

from ._artifact import RenderArtifact
from ._diagnostics import (
    build_render_diagnostics_report,
    log_render_diagnostics,
    serialize_render_diagnostics,
    serialize_render_diagnostics_report,
)
from ._svg_sppm_edges import _annotation_bounds_for_placement
from ._svg_sppm_edges import _edge_callout_placement
from ._svg_sppm_edges import _is_synthetic_sppm_lane
from ._svg_sppm_edges import _label_placement
from ._svg_sppm_edges import _lane_header_avoid_bounds
from ._svg_shared_primitives import (
    raw_node_lookup,
    standard_edge_svg,
    standard_lane_svg,
    standard_node_svg,
    standard_svg_defs,
)
from ._svg_sppm_rows import _display_canvas_bounds
from ._svg_sppm_rows import _enforce_sppm_row_alignment
from ._svg_sppm_rows import _sppm_row_ids
from ._svg_sppm_rows import rework_alignment_diagnostics
from ._svg_sppm_rows import row_gap_diagnostics
from .layout_core import build_sppm_elk_layout_request, execute_elk_layout
from .layout_core.elk_support import extract_nodes_and_edges
from .layout_core.elk_runtime import run_elkjs_layout
from .layout_core.models import LayoutBounds
from .options import RenderOptions
from ._sppm_publication import build_sppm_publication_plan

_PADDING = 28.0
_STRICT_POSTPROCESS_CODES = {
    "sppm-annotation-overlap-fallback",
    "sppm-attachment-miss-distance",
    "sppm-branch-alignment-delta",
    "sppm-return-alignment-delta",
}

__all__ = [
    "render_sppm_svg_artifact",
    "render_sppm_svg_artifact_from_layout",
    "_annotation_bounds_for_placement",
    "_edge_callout_placement",
    "_label_placement",
    "_lane_header_avoid_bounds",
    "rework_alignment_diagnostics",
    "row_gap_diagnostics",
]


def render_sppm_svg_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render a minimal standalone SVG for SPPM diagrams using ELK layout."""
    request = build_sppm_elk_layout_request(process, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    return render_sppm_svg_artifact_from_layout(
        process=process,
        options=options,
        request=request,
        result=result,
    )


def render_sppm_svg_artifact_from_layout(
    *,
    process: dict[str, Any] | Any,
    options: RenderOptions,
    request: Any,
    result: Any,
) -> tuple[RenderArtifact, None]:
    """Render SPPM SVG using a precomputed ELK request/result pair."""
    display_node_bounds, display_edge_paths = _enforce_sppm_row_alignment(
        node_bounds=result.node_bounds,
        edge_paths=result.edge_paths,
        lanes=result.lanes,
    )
    postprocess_diagnostics = list(
        row_gap_diagnostics(
            node_bounds=display_node_bounds,
            lanes=result.lanes,
            edge_paths=display_edge_paths,
        )
    )
    postprocess_diagnostics.extend(
        rework_alignment_diagnostics(
            node_bounds=display_node_bounds,
            lanes=result.lanes,
            edge_paths=display_edge_paths,
        )
    )
    display_canvas_bounds = _display_canvas_bounds(
        base_canvas=result.canvas_bounds,
        node_bounds=display_node_bounds,
        edge_paths=display_edge_paths,
    )
    raw_node_by_id = _raw_node_lookup(process, options=options)
    publication_plan = _build_sppm_publication_plan(
        process=process,
        options=options,
        request=request,
    )
    publication_page = publication_plan.primary_series().pages[0]
    header_band = publication_page.band("header")
    footer_band = publication_page.band("footer")
    header_height = float(header_band.region.height_px or 0) if header_band else 0.0
    footer_height = float(footer_band.region.height_px or 0) if footer_band else 0.0

    width = max(1.0, display_canvas_bounds.width_px + (_PADDING * 2.0))
    height = max(
        1.0,
        display_canvas_bounds.height_px
        + (_PADDING * 2.0)
        + header_height
        + footer_height,
    )
    content_top = _PADDING + header_height

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg" '
            'data-flo-diagram="sppm" data-flo-layout-engine="elk" '
            f'data-sppm-publication-page-id="{escape(publication_page.page_id)}"'
            ">"
        ),
        '<rect width="100%" height="100%" fill="#fffdf8" />',
    ]
    parts[1:1] = standard_svg_defs()

    parts.extend(
        _publication_band_svg(
            band=header_band,
            x=_PADDING,
            y=_PADDING,
            width=width - (_PADDING * 2.0),
        )
    )

    parts.append(f'<g transform="translate({_PADDING:.1f},{content_top:.1f})">')

    visible_lanes = tuple(
        lane for lane in result.lanes if not _is_synthetic_sppm_lane(lane.id)
    )
    for lane in visible_lanes:
        parts.extend(standard_lane_svg(lane))

    avoid_bounds = tuple(display_node_bounds.values()) + _lane_header_avoid_bounds(
        visible_lanes
    )
    canvas_bounds = display_canvas_bounds
    node_kind_by_id = {
        str(node.id): str(node.kind or "task").lower() for node in request.nodes
    }
    _mainline_ids, rework_ids = _sppm_row_ids(
        lanes=result.lanes,
        node_bounds=display_node_bounds,
        edge_paths=display_edge_paths,
    )
    occupied_annotation_bounds: list[LayoutBounds] = []
    for edge_key in sorted(display_edge_paths.keys()):
        source_id, target_id = edge_key
        edge_parts, annotation_bounds = standard_edge_svg(
            edge_path=display_edge_paths[edge_key],
            source_bounds=display_node_bounds.get(source_id),
            target_bounds=display_node_bounds.get(target_id),
            source_kind=node_kind_by_id.get(source_id, "task"),
            target_kind=node_kind_by_id.get(target_id, "task"),
            avoid_bounds=avoid_bounds + tuple(occupied_annotation_bounds),
            canvas_bounds=canvas_bounds,
            diagnostics=postprocess_diagnostics,
            render_as_rework_style=(
                source_id in rework_ids and target_id in rework_ids
            ),
        )
        parts.extend(edge_parts)
        occupied_annotation_bounds.extend(annotation_bounds)

    diagnostics = tuple(result.diagnostics) + tuple(postprocess_diagnostics)
    _raise_for_strict_postprocess_diagnostics(
        diagnostics=diagnostics,
        strict=options.layout_fit == "fit-strict",
    )
    diagnostics_report = build_render_diagnostics_report(
        diagnostics,
        diagram="sppm",
        backend="svg",
        artifact_kind="svg",
        strict=options.layout_fit == "fit-strict",
    )
    log_render_diagnostics(diagnostics_report)

    for node in request.nodes:
        bounds = display_node_bounds.get(node.id)
        if bounds is None:
            continue
        raw_node = raw_node_by_id.get(node.id, {})
        parts.extend(
            standard_node_svg(
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
    parts.extend(
        _publication_band_svg(
            band=footer_band,
            x=_PADDING,
            y=content_top + display_canvas_bounds.height_px,
            width=width - (_PADDING * 2.0),
        )
    )
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
                "publication": {
                    "page_id": publication_page.page_id,
                    "page_format": publication_page.metadata.get("page_format"),
                },
            },
        ),
        None,
    )


def _raise_for_strict_postprocess_diagnostics(
    *, diagnostics: tuple[Any, ...], strict: bool
) -> None:
    if not strict:
        return
    blocking = [
        diagnostic
        for diagnostic in diagnostics
        if getattr(diagnostic, "code", "") in _STRICT_POSTPROCESS_CODES
    ]
    if not blocking:
        return
    first = blocking[0]
    raise RenderError(
        "Strict SPPM post-process diagnostics failed: "
        f"{getattr(first, 'code', 'unknown')} - {getattr(first, 'message', '')}"
    )


def _raw_node_lookup(
    process: dict[str, Any] | Any, *, options: RenderOptions
) -> dict[str, dict[str, Any]]:
    return raw_node_lookup(process, options=options)


def _build_sppm_publication_plan(
    *, process: dict[str, Any] | Any, options: RenderOptions, request: Any
) -> Any:
    source_nodes, source_edges = extract_nodes_and_edges(process)
    visible_node_ids = {str(node.id) for node in request.nodes}
    nodes = [
        node for node in source_nodes if str(node.get("id") or "") in visible_node_ids
    ]
    edges = [
        edge
        for edge in source_edges
        if str(edge.get("source") or "") in visible_node_ids
        and str(edge.get("target") or "") in visible_node_ids
    ]
    return build_sppm_publication_plan(
        process=process,
        options=options,
        nodes=nodes,
        edges=edges,
    )


def _publication_band_svg(
    *, band: Any | None, x: float, y: float, width: float
) -> list[str]:
    if band is None:
        return []
    content = band.content
    line_y = y + 24.0
    parts = [
        f'<g data-sppm-publication-band="{escape(band.name)}">',
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + width:.1f}" y2="{y:.1f}" stroke="#cbd5e1" stroke-width="1" />',
    ]
    if content.title:
        parts.append(
            f'<text x="{x:.1f}" y="{line_y:.1f}" font-family="Helvetica" font-size="22" font-weight="700" fill="#0f172a">{escape(content.title)}</text>'
        )
        line_y += 24.0
    for label, value in (*content.rows, *content.context_rows):
        parts.append(
            f'<text x="{x:.1f}" y="{line_y:.1f}" font-family="Helvetica" font-size="12" fill="#334155">{escape(label)}: {escape(value)}</text>'
        )
        line_y += 16.0
    for note in content.notes:
        parts.append(
            f'<text x="{x:.1f}" y="{line_y:.1f}" font-family="Helvetica" font-size="12" fill="#334155">{escape(note)}</text>'
        )
        line_y += 16.0
    parts.append("</g>")
    return parts
