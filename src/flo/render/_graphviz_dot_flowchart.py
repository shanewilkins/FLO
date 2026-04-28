"""Flowchart DOT renderer helpers for FLO."""

from __future__ import annotations

from typing import Any

from ._autoformat_wrap import append_wrap_layout_hints, build_wrap_plan
from ._graphviz_dot_edge_routing import _append_edges
from ._graphviz_dot_common import (
    _append_clustered_node_passes,
    _build_nodes_by_id,
    _extract_nodes_and_edges,
    _node_lane_map,
    _project_parent_only_subprocess_view,
    _subprocess_children_map,
)
from .options import RenderOptions


def render_flowchart_dot(process: dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a simple flowchart DOT representation.

    Supports canonical IR objects and dict-based shapes.
    """
    render_options = options or RenderOptions()
    return _render_flowchart_graph(process, options=render_options)


def _render_flowchart_graph(process: dict[str, Any] | Any, options: RenderOptions) -> str:
    nodes, edges = _extract_nodes_and_edges(process)
    if options.subprocess_view == "parent_only":
        nodes, edges = _project_parent_only_subprocess_view(nodes, edges)
    node_lanes = _node_lane_map(nodes)
    wrap_plan = build_wrap_plan(nodes, options, planner="chunked")
    rankdir = _resolve_rankdir(options=options, wrap_active=wrap_plan.active)
    node_sequence_index = {
        str(node.get("id") or ""): idx
        for idx, node in enumerate(nodes)
        if str(node.get("id") or "")
    }

    lines: list[str] = ["digraph {"]
    lines.append(f"  rankdir={rankdir};")
    splines = "ortho" if wrap_plan.active else "true"
    lines.append(f"  graph [compound=true, newrank=true, nodesep=0.7, ranksep=0.9, splines={splines}];")
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    append_wrap_layout_hints(lines=lines, options=options, plan=wrap_plan)

    _append_flowchart_nodes(lines=lines, nodes=nodes, options=options)
    _append_edges(
        lines=lines,
        edges=edges,
        options=options,
        use_swimlanes=False,
        node_lanes=node_lanes,
        boundary_edges=wrap_plan.boundary_edges,
        node_sequence_index=node_sequence_index,
        wrap_active=wrap_plan.active,
    )

    lines.append("}")
    return "\n".join(lines)


def _resolve_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    return "TB" if options.orientation == "lr" else "LR"


def _append_flowchart_nodes(lines: list[str], nodes: list[dict[str, Any]], options: RenderOptions) -> None:
    nodes_by_id = _build_nodes_by_id(nodes)
    children_by_parent = _subprocess_children_map(nodes, nodes_by_id)
    _append_clustered_node_passes(
        lines=lines,
        ordered_nodes=nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        options=options,
        indent="  ",
    )
