"""Minimal direct-SVG SPPM renderer backed by ELK layout."""

from __future__ import annotations

from html import escape
from typing import Any

from .._artifact import RenderArtifact
from .._diagnostics import (
    build_render_diagnostics_report,
    serialize_render_diagnostics,
    serialize_render_diagnostics_report,
)
from .._execution import FinalScene, PositionedBand
from .._svg_theme import apply_svg_typography, svg_theme_metadata
from ..layout_core.elk_contracts import ElkLayoutRequest
from ..options import RenderOptions
from .edge_svg import emit_edge
from .primitives import (
    SVG_ACCESSIBILITY_ATTRIBUTES,
    raw_node_lookup,
    standard_lane_svg,
    standard_node_svg,
    standard_svg_defs,
    svg_accessibility_elements,
)


def emit_sppm_svg_artifact(
    *,
    process: dict[str, Any] | Any,
    options: RenderOptions,
    request: ElkLayoutRequest,
    scene: FinalScene,
) -> tuple[RenderArtifact, None]:
    """Serialize supplied final geometry; no attachment, placement, or avoidance."""
    display_node_bounds = scene.routed.node_bounds
    width, height = scene.width, scene.height
    raw_node_by_id = raw_node_lookup(process, options=options)
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg" '
            'data-flo-diagram="sppm" data-flo-layout-engine="elk" '
            f"{SVG_ACCESSIBILITY_ATTRIBUTES} "
            f'data-sppm-publication-page-id="{escape(scene.page_id)}"'
            ">"
        ),
        *svg_accessibility_elements(process, diagram_name="SPPM"),
        svg_theme_metadata(options),
        f'<rect width="100%" height="100%" fill="{options.resolved_theme.canvas_background}" />',
    ]
    parts[1:1] = standard_svg_defs(options)

    parts.extend(_publication_band_svg(scene.header, options))
    parts.append(
        f'<g transform="translate({scene.content_origin.x_px:.1f},{scene.content_origin.y_px:.1f})">'
    )
    for lane in scene.routed.lanes:
        parts.extend(standard_lane_svg(lane, options))
    for edge in scene.edges:
        parts.extend(emit_edge(edge, options))
    diagnostics = scene.diagnostics
    diagnostics_report = build_render_diagnostics_report(
        diagnostics,
        diagram="sppm",
        backend="svg",
        artifact_kind="svg",
        strict=options.layout_fit == "fit-strict",
    )
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
    parts.extend(_publication_band_svg(scene.footer, options))
    parts.append("</svg>")
    return (
        RenderArtifact(
            kind="svg",
            content=apply_svg_typography("\n".join(parts), options),
            backend="svg",
            metadata={
                "render_diagnostics": serialize_render_diagnostics(diagnostics),
                "render_diagnostics_report": serialize_render_diagnostics_report(
                    diagnostics_report
                ),
                "publication": {
                    "page_id": scene.page_id,
                    "page_format": scene.page_format,
                },
            },
        ),
        None,
    )


def _publication_band_svg(
    band: PositionedBand | None, options: RenderOptions
) -> list[str]:
    """Paint a supplied band line and its resolved text baselines."""
    if band is None:
        return []
    role = options.resolved_theme.role("publication")
    parts = [
        f'<g data-sppm-publication-band="{escape(band.name)}">',
        f'<line x1="{band.x:.1f}" y1="{band.y:.1f}" x2="{band.x + band.width:.1f}" y2="{band.y:.1f}" stroke="{role.border}" stroke-width="1" />',
    ]
    for text in band.texts:
        weight = f' font-weight="{text.weight}"' if text.weight else ""
        fill = getattr(role, text.role_field)
        parts.append(
            f'<text x="{text.x:.1f}" y="{text.y:.1f}" font-family="Helvetica" font-size="{text.size_px}"{weight} fill="{fill}">{escape(text.text)}</text>'
        )
    parts.append("</g>")
    return parts
