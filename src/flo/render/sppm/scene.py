"""Complete SPPM geometry before SVG serialization, including publication bands."""

from __future__ import annotations

from typing import Any

from flo.errors import RenderError
from flo.process.analysis import ProcessTimingAnalysis

from .._execution import FinalScene, PositionedBand, PositionedText, RoutedGeometry
from .._publication import PublicationBand
from ..layout_core.elk_contracts import ElkLayoutRequest
from ..layout_core.elk_support import extract_nodes_and_edges
from ..layout_core.models import LayoutBounds, LayoutPoint
from ..options import RenderOptions
from .avoidance import node_avoid_bounds
from .edge_geometry import prepare_edge
from .edge_layout import _lane_header_avoid_bounds
from .publication import build_sppm_publication_plan

_PADDING = 28.0
_STRICT_POSTPROCESS_CODES = {
    "sppm-annotation-overlap-fallback",
    "sppm-attachment-miss-distance",
    "sppm-branch-alignment-delta",
    "sppm-return-alignment-delta",
}


def finalize_sppm_scene(
    *,
    process: Any,
    options: RenderOptions,
    request: ElkLayoutRequest,
    geometry: RoutedGeometry,
    timing_analysis: ProcessTimingAnalysis | None = None,
) -> FinalScene:
    """Materialize attachments, annotations, occupied bounds, diagnostics, and bands."""
    plan = _build_sppm_publication_plan(
        process=process,
        options=options,
        request=request,
        timing_analysis=timing_analysis,
    )
    page = plan.primary_series().pages[0]
    header, footer = page.band("header"), page.band("footer")
    header_height = float(header.region.height_px or 0) if header else 0.0
    footer_height = float(footer.region.height_px or 0) if footer else 0.0
    width = max(1.0, geometry.canvas_bounds.width_px + _PADDING * 2)
    height = max(
        1.0,
        geometry.canvas_bounds.height_px + _PADDING * 2 + header_height + footer_height,
    )
    top = _PADDING + header_height
    kinds = {str(node.id): str(node.kind or "task").lower() for node in request.nodes}
    avoid = tuple(
        box
        for node, bounds in geometry.node_bounds.items()
        for box in node_avoid_bounds(bounds, kinds.get(node, "task"))
    ) + _lane_header_avoid_bounds(geometry.lanes)
    occupied: list[LayoutBounds] = []
    edges = []
    diagnostics = list(geometry.diagnostics)
    for key, path in sorted(geometry.edge_paths.items()):
        edge = prepare_edge(
            path,
            options=options,
            source_bounds=geometry.node_bounds.get(key[0]),
            target_bounds=geometry.node_bounds.get(key[1]),
            source_kind=kinds.get(key[0], "task"),
            target_kind=kinds.get(key[1], "task"),
            avoid_bounds=avoid + tuple(occupied),
            canvas_bounds=geometry.canvas_bounds,
            diagnostics=diagnostics,
            render_as_rework_style=key in geometry.edge_groups["correction"],
        )
        edges.append(edge)
        occupied.extend(annotation.bounds for annotation in edge.annotations)
    _raise_for_strict_postprocess_diagnostics(
        diagnostics=tuple(diagnostics), strict=options.layout_fit == "fit-strict"
    )
    return FinalScene(
        geometry,
        tuple(edges),
        tuple(occupied),
        tuple(diagnostics),
        width,
        height,
        LayoutPoint(_PADDING, top),
        page.page_id,
        page.metadata.get("page_format"),
        _place_band(header, _PADDING, _PADDING, width - _PADDING * 2, options),
        _place_band(
            footer,
            _PADDING,
            top + geometry.canvas_bounds.height_px,
            width - _PADDING * 2,
            options,
        ),
    )


def _place_band(
    band: PublicationBand | None,
    x: float,
    y: float,
    width: float,
    options: RenderOptions,
) -> PositionedBand | None:
    if band is None:
        return None
    content = band.content
    scale = options.resolved_theme.typography_scale
    line_y = y + 24.0 * scale
    texts = []
    if content.title:
        texts.append(PositionedText(content.title, x, line_y, "start", 22, "700"))
        line_y += 24.0 * scale
    for label, value in (*content.rows, *content.context_rows):
        texts.append(
            PositionedText(
                f"{label}: {value}", x, line_y, "start", 12, role_field="detail_text"
            )
        )
        line_y += 16.0 * scale
    for note in content.notes:
        texts.append(
            PositionedText(note, x, line_y, "start", 12, role_field="detail_text")
        )
        line_y += 16.0 * scale
    return PositionedBand(band.name, x, y, width, tuple(texts))


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


def _build_sppm_publication_plan(
    *,
    process: dict[str, Any] | Any,
    options: RenderOptions,
    request: Any,
    timing_analysis: ProcessTimingAnalysis | None = None,
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
        timing_analysis=timing_analysis,
    )
