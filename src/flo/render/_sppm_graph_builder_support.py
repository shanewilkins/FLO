"""Support helpers for SPPM graph assembly."""

from __future__ import annotations

from typing import Any

from ._autoformat_wrap import WrapPlan, append_wrap_layout_hints
from ._sppm_band_render import render_sppm_footer_band
from ._sppm_edge_render import (
    _render_sppm_edge,
    _render_sppm_secondary_line_constraints,
    _render_sppm_spine_constraints,
)
from ._sppm_node_render import render_sppm_node
from ._sppm_routing import SppmRoutingPlan
from ._sppm_themes import SppmTheme
from .options import RenderOptions


def build_sppm_graph_preamble_lines(*, lines: list[str], rankdir: str, nodesep: float, ranksep: float) -> None:
    """Append the fixed graph preamble lines for an SPPM render."""
    lines.append(f"  rankdir={rankdir};")
    lines.append(
        f"  graph [compound=true, newrank=true, nodesep={nodesep}, ranksep={ranksep}, margin=0.05, pad=0.05, splines=ortho, bgcolor=white];"
    )
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")


def append_sppm_graph_layout_hints(*, lines: list[str], options: RenderOptions, plan: WrapPlan) -> None:
    """Append optional wrap-related layout hints."""
    append_wrap_layout_hints(lines=lines, options=options, plan=plan)


def append_sppm_graph_node_lines(
    *,
    lines: list[str],
    nodes: list[dict[str, Any]],
    options: RenderOptions,
    theme: SppmTheme,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    port_counts: dict[str, dict[str, int]],
) -> None:
    """Append rendered node lines for the graph."""
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


def append_sppm_graph_edge_lines(
    *,
    lines: list[str],
    edges: list[dict[str, Any]],
    nodes_by_id: dict[str, Any],
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    routing_plan: SppmRoutingPlan,
) -> None:
    """Append rendered edge lines for the graph."""
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


def append_sppm_graph_constraint_lines(
    *,
    lines: list[str],
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> None:
    """Append the invisible spine and secondary-line constraints."""
    lines.extend(_render_sppm_spine_constraints(edges=edges, routing_plan=routing_plan))
    lines.extend(_render_sppm_secondary_line_constraints(edges=edges, routing_plan=routing_plan))


def append_sppm_graph_footer_lines(
    *,
    lines: list[str],
    publication: Any,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    """Append the publication-backed footer band lines."""
    lines.extend(render_sppm_footer_band(publication=publication, nodes=nodes, edges=edges))