"""Minimal direct-SVG flowchart renderer backed by ELK layout."""

from __future__ import annotations

import warnings
from typing import Any

from ._artifact import RenderArtifact
from ._diagnostics import (
    log_render_diagnostics,
    serialize_render_diagnostics,
    serialize_render_diagnostics_report,
)
from ._svg_shared_primitives import (
    raw_node_lookup,
    standard_edge_svg,
    standard_node_svg,
    standard_svg_defs,
)
from .layout_core import build_flowchart_elk_layout_request, execute_elk_layout
from .layout_core.elk_runtime import run_elkjs_layout
from .options import RenderOptions

_PADDING = 24.0
_FLOWCHART_DEPRECATION_WARNED = False


def _warn_flowchart_deprecated_once() -> None:
    global _FLOWCHART_DEPRECATION_WARNED
    if _FLOWCHART_DEPRECATION_WARNED:
        return
    warnings.warn(
        "Flowchart direct SVG rendering is deprecated and will be removed in 0.2.0. "
        "Use swimlane or sppm diagrams for forward-compatible rendering.",
        DeprecationWarning,
        stacklevel=2,
    )
    _FLOWCHART_DEPRECATION_WARNED = True


def render_flowchart_svg_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render a minimal standalone SVG for flowcharts using ELK layout."""
    _warn_flowchart_deprecated_once()
    request = build_flowchart_elk_layout_request(process, options=options)
    result = execute_elk_layout(request, engine=run_elkjs_layout)
    diagnostics_report = result.diagnostics_report(
        diagram="flowchart",
        backend="svg",
        artifact_kind="svg",
        strict=options.layout_fit == "fit-strict",
    )
    log_render_diagnostics(diagnostics_report)
    node_by_id = {node.id: node for node in request.nodes}
    raw_node_by_id = raw_node_lookup(process, options=options)

    width = max(1.0, result.canvas_bounds.width_px + (_PADDING * 2.0))
    height = max(1.0, result.canvas_bounds.height_px + (_PADDING * 2.0))

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg" '
            'data-flo-diagram="flowchart" data-flo-layout-engine="elk">'
        ),
        '<rect width="100%" height="100%" fill="#fffdf8" />',
        f'<g transform="translate({_PADDING:.1f},{_PADDING:.1f})">',
    ]
    parts[1:1] = standard_svg_defs()

    for edge_key in sorted(result.edge_paths.keys()):
        source_id, target_id = edge_key
        edge_parts, _annotation_bounds = standard_edge_svg(
            edge_path=result.edge_paths[edge_key],
            source_bounds=result.node_bounds.get(source_id),
            target_bounds=result.node_bounds.get(target_id),
            source_kind=str(
                getattr(node_by_id.get(source_id), "kind", "task") or "task"
            ).lower(),
            target_kind=str(
                getattr(node_by_id.get(target_id), "kind", "task") or "task"
            ).lower(),
            avoid_bounds=tuple(result.node_bounds.values()),
            canvas_bounds=result.canvas_bounds,
            diagnostics=[],
            render_as_rework_style=False,
        )
        parts.extend(edge_parts)

    for node_id in [node.id for node in request.nodes]:
        bounds = result.bounds_for(node_id)
        if bounds is None:
            continue
        node = node_by_id.get(node_id)
        if node is None:
            continue
        parts.extend(
            standard_node_svg(
                node=node,
                raw_node=raw_node_by_id.get(node.id, {}),
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
                "render_diagnostics": serialize_render_diagnostics(result.diagnostics),
                "render_diagnostics_report": serialize_render_diagnostics_report(
                    diagnostics_report
                ),
            },
        ),
        None,
    )
