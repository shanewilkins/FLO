"""Swimlane DOT renderer helpers for FLO."""

from __future__ import annotations

from typing import Any

from ._autoformat_wrap import append_wrap_layout_hints, build_autoformat_wrap_plan
from ._graphviz_dot_common import (
    _append_clustered_node_passes,
    _append_edges,
    _build_nodes_by_id,
    _escape,
    _extract_nodes_and_edges,
    _node_lane_map,
    _project_parent_only_subprocess_view,
    _safe_cluster_id,
    _subprocess_children_map,
)
from .options import RenderOptions


def render_swimlane_dot(process: dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a swimlane-style DOT graph.

    Swimlane mode groups nodes by lane in cluster subgraphs.
    """
    render_options = options or RenderOptions(diagram="swimlane")
    return _render_swimlane_graph(process, options=render_options)


def _render_swimlane_graph(process: dict[str, Any] | Any, options: RenderOptions) -> str:
    nodes, edges = _extract_nodes_and_edges(process)
    if options.subprocess_view == "parent_only":
        nodes, edges = _project_parent_only_subprocess_view(nodes, edges)
    node_lanes = _node_lane_map(nodes)
    wrap_plan = build_autoformat_wrap_plan(nodes, options)
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

    _append_swimlane_nodes(lines=lines, nodes=nodes, options=options)
    _append_edges(
        lines=lines,
        edges=edges,
        options=options,
        use_swimlanes=True,
        node_lanes=node_lanes,
        boundary_edges=wrap_plan.boundary_edges,
        node_sequence_index=node_sequence_index,
    )

    lines.append("}")
    return "\n".join(lines)


def _resolve_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    return "TB" if options.orientation == "lr" else "LR"


def _append_swimlane_nodes(lines: list[str], nodes: list[dict[str, Any]], options: RenderOptions) -> None:
    lane_groups, unlaned_nodes = _partition_nodes_by_lane(nodes)
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id:
            nodes_by_id[node_id] = node

    children_by_parent = _subprocess_children_map(nodes, nodes_by_id)

    lane_specs = [(lane_name, lane_nodes, _safe_cluster_id(lane_name)) for lane_name, lane_nodes in lane_groups.items()]
    if unlaned_nodes:
        lane_specs.append(("unassigned", unlaned_nodes, "unassigned"))

    left_boundary_nodes: list[str] = []
    right_boundary_nodes: list[str] = []

    for lane_index, (lane_name, lane_nodes, lane_id) in enumerate(lane_specs):
        left_anchor = f"__lane_{lane_id}_left"
        right_anchor = f"__lane_{lane_id}_right"
        left_boundary_nodes.append(left_anchor)
        right_boundary_nodes.append(right_anchor)

        lines.append(f"  subgraph cluster_{lane_id} {{")
        lines.append(f'    label="{_escape(str(lane_name))}";')
        lines.append('    style="rounded,filled";')
        lines.append("    penwidth=2;")
        lines.append("    color=gray55;")
        lines.append(f'    fillcolor="{_lane_fillcolor(lane_index)}";')
        lines.append("    labelloc=t;")
        lines.append("    labeljust=l;")
        lines.append(f'    "{left_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')
        lines.append(f'    "{right_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')

        _append_swimlane_lane_nodes(
            lines=lines,
            lane_nodes=lane_nodes,
            children_by_parent=children_by_parent,
            options=options,
        )

        lane_node_ids = [str(node.get("id") or "") for node in lane_nodes if str(node.get("id") or "")]

        _append_lane_spine(
            lines=lines,
            left_anchor=left_anchor,
            right_anchor=right_anchor,
            lane_node_ids=lane_node_ids,
        )

        lines.append("  }")

    _append_lane_boundary_subgraphs(lines, left_boundary_nodes, right_boundary_nodes)
    _append_lane_boundary_guides(lines, left_boundary_nodes, right_boundary_nodes)


def _append_swimlane_lane_nodes(
    lines: list[str],
    lane_nodes: list[dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    options: RenderOptions,
) -> None:
    lane_nodes_by_id = _build_nodes_by_id(lane_nodes)
    _append_clustered_node_passes(
        lines=lines,
        ordered_nodes=lane_nodes,
        nodes_by_id=lane_nodes_by_id,
        children_by_parent=children_by_parent,
        options=options,
        indent="    ",
    )


def _partition_nodes_by_lane(nodes: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    lane_groups: dict[str, list[dict[str, Any]]] = {}
    unlaned_nodes: list[dict[str, Any]] = []

    for node in nodes:
        lane = node.get("lane")
        if lane is None or str(lane).strip() == "":
            unlaned_nodes.append(node)
            continue
        lane_key = str(lane)
        lane_groups.setdefault(lane_key, []).append(node)

    return lane_groups, unlaned_nodes


def _lane_fillcolor(index: int) -> str:
    palette = ["gray96", "gray93"]
    return palette[index % len(palette)]


def _append_lane_boundary_subgraphs(lines: list[str], left_nodes: list[str], right_nodes: list[str]) -> None:
    if left_nodes:
        lines.append("  subgraph lane_left_boundary {")
        lines.append("    rank=same;")
        for node in left_nodes:
            lines.append(f'    "{node}";')
        lines.append("  }")

    if right_nodes:
        lines.append("  subgraph lane_right_boundary {")
        lines.append("    rank=same;")
        for node in right_nodes:
            lines.append(f'    "{node}";')
        lines.append("  }")


def _append_lane_boundary_guides(lines: list[str], left_nodes: list[str], right_nodes: list[str]) -> None:
    for boundary_nodes in (left_nodes, right_nodes):
        for source, target in zip(boundary_nodes, boundary_nodes[1:]):
            lines.append(
                f'  "{source}" -> "{target}" [style=invis, weight=200, minlen=1];'
            )


def _append_lane_spine(
    lines: list[str],
    left_anchor: str,
    right_anchor: str,
    lane_node_ids: list[str],
) -> None:
    chain: list[str] = [left_anchor, *[_escape(node_id) for node_id in lane_node_ids], right_anchor]
    if len(chain) < 2:
        return

    for source, target in zip(chain, chain[1:]):
        lines.append(
            f'    "{source}" -> "{target}" [style=invis, weight=200, minlen=2];'
        )
