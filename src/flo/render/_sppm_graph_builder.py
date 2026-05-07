"""Graph assembly for SPPM DOT output.

This module coordinates the already-separated SPPM concerns:
- render-data normalization
- wrap and routing plans
- node rendering
- publication-backed header/footer bands

The public SPPM entrypoint stays thin so future renderers can follow the same
shape without inheriting one monolithic implementation file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._autoformat_wrap import append_wrap_layout_hints, build_wrap_plan
from ._sppm_band_render import build_sppm_header, render_sppm_footer_band
from ._sppm_edge_render import (
    _render_sppm_edge,
    _render_sppm_secondary_line_constraints,
    _render_sppm_spine_constraints,
)
from ._sppm_node_render import render_sppm_node
from ._sppm_projection import project_sppm_subprocess_view
from ._sppm_publication import build_sppm_publication_plan
from ._sppm_render_data import (
    SppmRenderNode,
    build_step_numbering,
    extract_sppm_nodes_edges,
    port_counts_by_node,
)
from ._sppm_routing import build_sppm_routing_plan
from ._sppm_themes import resolve_sppm_theme
from .options import RenderOptions

if TYPE_CHECKING:
    from flo.compiler.ir.models import IR
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract

__all__ = ["build_sppm_graph"]


def build_sppm_graph(
    process: IR | dict[str, Any],
    *,
    options: RenderOptions,
) -> tuple[str, SppmSvgPostprocessContract]:
    """Return DOT and postprocess contract for an SPPM render request."""
    nodes, edges = extract_sppm_nodes_edges(process)
    nodes, edges, projection = project_sppm_subprocess_view(nodes, edges, options=options)

    publication = build_sppm_publication_plan(
        process=process,
        options=options,
        nodes=nodes,
        edges=edges,
        projection=projection,
    )
    header = build_sppm_header(publication=publication)

    nodes_by_id: dict[str, SppmRenderNode] = {str(node.get("id", "")): node for node in nodes if node.get("id")}
    step_numbering = build_step_numbering(nodes)
    wrap_plan = build_wrap_plan(nodes, options, planner="placement")
    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
        edges=edges,
        options=options,
        step_numbering=step_numbering,
        wrap_plan=wrap_plan,
    )
    contract = routing_plan.svg_postprocess_contract
    port_counts = port_counts_by_node(routing_plan)
    theme = resolve_sppm_theme(options.sppm_theme)

    lines: list[str] = ["digraph {"]
    rankdir = _resolve_rankdir(options=options, wrap_active=wrap_plan.active)
    lines.append(f"  rankdir={rankdir};")
    nodesep, ranksep = _sppm_graph_spacing(options=options, wrap_active=wrap_plan.active)
    lines.append(
        f"  graph [compound=true, newrank=true, nodesep={nodesep}, ranksep={ranksep}, margin=0.05, pad=0.05, splines=ortho, bgcolor=white];"
    )
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    if header:
        lines.append("  labelloc=t;")
        lines.append('  labeljust=l;')
        lines.append(f"  label={header};")

    append_wrap_layout_hints(lines=lines, options=options, plan=wrap_plan)

    for node in nodes:
        lines.extend(
            render_sppm_node(
                node,
                options=options,
                theme=theme,
                step_numbering=step_numbering,
                wrap_plan=wrap_plan,
                port_counts=port_counts.get(str(node.get("id") or ""), {}),
            )
        )

    for edge in edges:
        lines.extend(
            _render_sppm_edge(
                edge,
                nodes_by_id=nodes_by_id,
                options=options,
                step_numbering=step_numbering,
                wrap_plan=wrap_plan,
                route=routing_plan.route_for(str(edge.get("source") or ""), str(edge.get("target") or "")),
            )
        )

    lines.extend(_render_sppm_spine_constraints(edges=edges, routing_plan=routing_plan))
    lines.extend(_render_sppm_secondary_line_constraints(edges=edges, routing_plan=routing_plan))
    lines.extend(render_sppm_footer_band(publication=publication, nodes=nodes, edges=edges))
    lines.append("}")
    return "\n".join(lines), contract


def _resolve_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    return "TB" if options.orientation == "lr" else "LR"


def _sppm_graph_spacing(*, options: RenderOptions, wrap_active: bool) -> tuple[float, float]:
    if not wrap_active:
        if options.layout_spacing == "compact":
            return 0.75, 1.0
        return 0.9, 1.2
    if options.layout_fit == "fit-strict":
        if options.layout_spacing == "compact":
            return 0.25, 0.3
        return 0.3, 0.35
    if options.layout_spacing == "compact":
        return 0.35, 0.3
    return 0.4, 0.35