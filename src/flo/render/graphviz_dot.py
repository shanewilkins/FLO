"""Graphviz DOT renderers for FLO models."""

from __future__ import annotations

from typing import Any, Dict

from .options import RenderOptions


def render_flowchart_dot(process: Dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a simple flowchart DOT representation.

    Supports canonical IR objects and dict-based shapes.
    """
    return _render_dot_graph(process, options=options or RenderOptions(), use_swimlanes=False)


def render_swimlane_dot(process: Dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a swimlane-style DOT graph.

    Swimlane mode groups nodes by lane in cluster subgraphs.
    """
    render_options = options or RenderOptions(diagram="swimlane")
    return _render_dot_graph(process, options=render_options, use_swimlanes=True)


def _render_dot_graph(process: Dict[str, Any] | Any, options: RenderOptions, use_swimlanes: bool) -> str:
    nodes, edges = _extract_nodes_and_edges(process)
    node_lanes = _node_lane_map(nodes)
    rankdir = "TB" if options.orientation == "tb" else "LR"

    lines: list[str] = ["digraph {"]
    lines.append(f"  rankdir={rankdir};")
    lines.append("  graph [compound=true, newrank=true, nodesep=0.7, ranksep=0.9, splines=true];")
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    if use_swimlanes:
        _append_swimlane_nodes(lines=lines, nodes=nodes, options=options)
    else:
        for node in nodes:
            lines.extend(_render_node_line(node, indent="  ", options=options))

    _append_edges(lines=lines, edges=edges, options=options, use_swimlanes=use_swimlanes, node_lanes=node_lanes)

    lines.append("}")
    return "\n".join(lines)


def _append_swimlane_nodes(lines: list[str], nodes: list[dict[str, Any]], options: RenderOptions) -> None:
    lane_groups, unlaned_nodes = _partition_nodes_by_lane(nodes)
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
        lines.append("    style=\"rounded,filled\";")
        lines.append("    penwidth=2;")
        lines.append("    color=gray55;")
        lines.append(f'    fillcolor="{_lane_fillcolor(lane_index)}";')
        lines.append("    labelloc=t;")
        lines.append("    labeljust=l;")
        lines.append(f'    "{left_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')
        lines.append(f'    "{right_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')

        lane_node_ids: list[str] = []
        for node in lane_nodes:
            node_id = str(node.get("id", ""))
            lines.extend(_render_node_line(node, indent="    ", options=options))
            if node_id:
                lane_node_ids.append(node_id)

        _append_lane_spine(
            lines=lines,
            left_anchor=left_anchor,
            right_anchor=right_anchor,
            lane_node_ids=lane_node_ids,
        )

        lines.append("  }")

    _append_lane_boundary_subgraphs(lines, left_boundary_nodes, right_boundary_nodes)
    _append_lane_boundary_guides(lines, left_boundary_nodes, right_boundary_nodes)


def _append_edges(
    lines: list[str],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
) -> None:
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        edge_attrs = _edge_attrs(
            edge=edge,
            source=str(source),
            target=str(target),
            options=options,
            use_swimlanes=use_swimlanes,
            node_lanes=node_lanes,
        )
        lines.append(
            f'  "{_escape(str(source))}" -> "{_escape(str(target))}" '
            f'[{", ".join(edge_attrs)}];'
        )


def _edge_attrs(
    edge: dict[str, Any],
    source: str,
    target: str,
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
) -> list[str]:
    edge_attrs: list[str] = []
    if use_swimlanes and _is_cross_lane_edge(source, target, node_lanes):
        # Keep lane centerlines stable: cross-lane flow should not re-rank lanes.
        edge_attrs.append("constraint=false")

    if options.detail != "summary":
        branch_label = edge.get("outcome") or edge.get("label")
        if branch_label is not None:
            edge_attrs.append(f'label="{_escape(str(branch_label))}"')

    return edge_attrs


def _extract_nodes_and_edges(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if process is None:
        return [], []

    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_from_ir_object(process)

    if isinstance(process, dict):
        return _extract_from_dict(process)

    return [], []


def _node_lane_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        out[node_id] = str(node.get("lane") or "")
    return out


def _is_cross_lane_edge(source: str, target: str, node_lanes: dict[str, str]) -> bool:
    source_lane = node_lanes.get(source, "")
    target_lane = node_lanes.get(target, "")
    if not source_lane or not target_lane:
        return False
    return source_lane != target_lane


def _extract_from_ir_object(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    for node in getattr(process, "nodes", []) or []:
        attrs = getattr(node, "attrs", {}) or {}
        name = attrs.get("name") if isinstance(attrs, dict) else None
        lane = attrs.get("lane") if isinstance(attrs, dict) else None
        note = attrs.get("note") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": name,
                "lane": lane,
                "note": note,
            }
        )

    edges = []
    for edge in getattr(process, "edges", []) or []:
        edges.append(
            {
                "source": getattr(edge, "source", None),
                "target": getattr(edge, "target", None),
                "outcome": getattr(edge, "outcome", None),
                "label": getattr(edge, "label", None),
            }
        )
    return nodes, edges


def _extract_from_dict(process: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_raw = process.get("nodes") or []
    edges_raw = process.get("edges") or []
    nodes = [n for n in nodes_raw if isinstance(n, dict)]
    edges = [e for e in edges_raw if isinstance(e, dict)]
    return nodes, edges


def _shape_for_kind(kind: str) -> str:
    norm = (kind or "task").lower()
    if norm == "start":
        return "ellipse"
    if norm == "end":
        return "ellipse"
    if norm == "decision":
        return "diamond"
    if norm == "queue":
        return "box"
    return "box"


def _node_label(node_id: str, name: str, kind: str, lane: str, note: str, options: RenderOptions) -> str:
    if options.detail == "summary":
        base = name or node_id
        return _with_note(base, note, options)

    if options.detail == "verbose":
        base = name or node_id
        if options.profile == "analysis":
            if lane:
                return _with_note(f"{base}\\n{node_id}\\n[{kind}|lane:{lane}]", note, options)
            return _with_note(f"{base}\\n{node_id}\\n[{kind}]", note, options)
        return _with_note(f"{base}\\n{node_id}", note, options)

    # standard
    return _with_note(name or node_id, note, options)


def _render_node_line(node: dict[str, Any], indent: str, options: RenderOptions) -> list[str]:
    node_id = str(node.get("id", ""))
    if not node_id:
        return []
    kind = str(node.get("kind") or node.get("type") or "task")
    lane = str(node.get("lane") or "")
    note = str(node.get("note") or "")
    label_name = str(node.get("name") or node_id)
    label = _node_label(node_id=node_id, name=label_name, kind=kind, lane=lane, note=note, options=options)
    shape = _shape_for_kind(kind)
    node_attrs = [f'label="{_escape(label)}"', f"shape={shape}"]
    if shape == "diamond":
        # Keep decision diamonds visually balanced instead of overly wide.
        node_attrs.append("regular=true")
    return [f'{indent}"{_escape(node_id)}" [{", ".join(node_attrs)}];']


def _with_note(base: str, note: str, options: RenderOptions) -> str:
    if not options.show_notes:
        return base
    note_text = " ".join((note or "").split())
    if not note_text:
        return base
    return f"{base}\\n\\nNote: {note_text}"


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


def _safe_cluster_id(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch in {"_", "-"}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    out = "".join(cleaned).strip("_")
    return out or "lane"


def _escape(text: str) -> str:
    return text.replace('"', '\\"')
