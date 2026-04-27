"""Shared Graphviz DOT helpers for flowchart and swimlane renderers."""

from __future__ import annotations

from typing import Any

from .options import RenderOptions

def _project_parent_only_subprocess_view(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hidden_ids, visible_ids, visible_nodes = _partition_subprocess_view_nodes(nodes)

    if not hidden_ids:
        return nodes, edges
    outgoing = _index_outgoing_edges(edges)
    collapsed_edges = _collapse_parent_only_edges(
        visible_ids=visible_ids,
        hidden_ids=hidden_ids,
        outgoing=outgoing,
    )
    return visible_nodes, collapsed_edges


def _partition_subprocess_view_nodes(
    nodes: list[dict[str, Any]],
) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    hidden_ids: set[str] = set()
    visible_ids: set[str] = set()

    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        if _subprocess_parent(node):
            hidden_ids.add(node_id)
        else:
            visible_ids.add(node_id)

    visible_nodes = [
        node
        for node in nodes
        if (node_id := str(node.get("id") or "")) and node_id in visible_ids
    ]
    return hidden_ids, visible_ids, visible_nodes


def _index_outgoing_edges(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        outgoing.setdefault(source, []).append(edge)
    return outgoing


def _collapse_parent_only_edges(
    visible_ids: set[str],
    hidden_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    collapsed_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None]] = set()

    for source in visible_ids:
        for edge in outgoing.get(source, []):
            target = str(edge.get("target") or "")
            if not target:
                continue

            branch_label = _edge_branch_label(edge)
            if target in visible_ids:
                _add_collapsed_edge(
                    collapsed_edges=collapsed_edges,
                    seen_edges=seen_edges,
                    source=source,
                    target=target,
                    branch_label=branch_label,
                )
                continue
            if target not in hidden_ids:
                continue

            for nested_target, next_label in _visible_targets_through_hidden(
                start_hidden=target,
                initial_label=branch_label,
                hidden_ids=hidden_ids,
                visible_ids=visible_ids,
                outgoing=outgoing,
            ):
                _add_collapsed_edge(
                    collapsed_edges=collapsed_edges,
                    seen_edges=seen_edges,
                    source=source,
                    target=nested_target,
                    branch_label=next_label,
                )

    return collapsed_edges


def _add_collapsed_edge(
    collapsed_edges: list[dict[str, Any]],
    seen_edges: set[tuple[str, str, str | None]],
    source: str,
    target: str,
    branch_label: str | None,
) -> None:
    if source == target:
        return
    edge_key = (source, target, branch_label)
    if edge_key in seen_edges:
        return
    seen_edges.add(edge_key)

    edge: dict[str, Any] = {"source": source, "target": target}
    if branch_label is not None:
        edge["label"] = branch_label
    collapsed_edges.append(edge)


def _visible_targets_through_hidden(
    start_hidden: str,
    initial_label: str | None,
    hidden_ids: set[str],
    visible_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, str | None]]:
    targets: list[tuple[str, str | None]] = []
    pending: list[tuple[str, str | None]] = [(start_hidden, initial_label)]
    visited_hidden: set[tuple[str, str | None]] = set()

    while pending:
        hidden_id, active_label = pending.pop()
        hidden_state = (hidden_id, active_label)
        if hidden_state in visited_hidden:
            continue
        visited_hidden.add(hidden_state)

        for nested_edge in outgoing.get(hidden_id, []):
            nested_target = str(nested_edge.get("target") or "")
            if not nested_target:
                continue

            next_label = active_label or _edge_branch_label(nested_edge)
            if nested_target in visible_ids:
                targets.append((nested_target, next_label))
            elif nested_target in hidden_ids:
                pending.append((nested_target, next_label))

    return targets


def _edge_branch_label(edge: dict[str, Any]) -> str | None:
    outcome = edge.get("outcome")
    if outcome is not None:
        text = str(outcome).strip()
        return text or None

    label = edge.get("label")
    if label is not None:
        text = str(label).strip()
        return text or None

    return None



def _build_nodes_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        nodes_by_id[node_id] = node
    return nodes_by_id


def _append_clustered_node_passes(
    lines: list[str],
    ordered_nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    options: RenderOptions,
    indent: str,
) -> None:
    rendered: set[str] = set()
    active_stack: set[str] = set()

    _append_clustered_node_pass(
        lines=lines,
        ordered_nodes=ordered_nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        rendered=rendered,
        active_stack=active_stack,
        options=options,
        indent=indent,
        top_level_only=True,
    )
    _append_clustered_node_pass(
        lines=lines,
        ordered_nodes=ordered_nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        rendered=rendered,
        active_stack=active_stack,
        options=options,
        indent=indent,
        top_level_only=False,
    )


def _append_clustered_node_pass(
    lines: list[str],
    ordered_nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    rendered: set[str],
    active_stack: set[str],
    options: RenderOptions,
    indent: str,
    top_level_only: bool,
) -> None:
    for node in ordered_nodes:
        node_id = str(node.get("id") or "")
        if not node_id or node_id in rendered:
            continue
        if top_level_only and _has_visible_parent(node, nodes_by_id):
            continue
        _append_node_or_subprocess_cluster(
            lines=lines,
            node_id=node_id,
            nodes_by_id=nodes_by_id,
            children_by_parent=children_by_parent,
            rendered=rendered,
            active_stack=active_stack,
            options=options,
            indent=indent,
        )


def _has_visible_parent(node: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> bool:
    parent_id = _subprocess_parent(node)
    return bool(parent_id and parent_id in nodes_by_id)


def _subprocess_children_map(
    nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    children_by_parent: dict[str, list[str]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        parent_id = _subprocess_parent(node)
        if not node_id or not parent_id or parent_id not in nodes_by_id:
            continue
        children_by_parent.setdefault(parent_id, []).append(node_id)
    return children_by_parent


def _append_node_or_subprocess_cluster(
    lines: list[str],
    node_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    rendered: set[str],
    active_stack: set[str],
    options: RenderOptions,
    indent: str,
) -> None:
    if node_id in rendered:
        return

    node = nodes_by_id.get(node_id)
    if node is None:
        return

    if node_id in active_stack:
        lines.extend(_render_node_line(node, indent=indent, options=options))
        rendered.add(node_id)
        return

    active_stack.add(node_id)

    child_ids = [child_id for child_id in children_by_parent.get(node_id, []) if child_id in nodes_by_id]
    kind = str(node.get("kind") or node.get("type") or "task").strip().lower()
    has_subprocess_children = kind == "subprocess" and bool(child_ids)

    if has_subprocess_children:
        cluster_id = _safe_cluster_id(f"subprocess_{node_id}")
        cluster_label = str(node.get("name") or node_id)
        lines.append(f"{indent}subgraph cluster_{cluster_id} {{")
        lines.append(f'{indent}  label="{_escape(cluster_label)}";')
        lines.append(f'{indent}  style="rounded,dashed";')
        lines.append(f"{indent}  penwidth=1.6;")
        lines.append(f"{indent}  color=gray55;")
        lines.append(f'{indent}  fillcolor="gray98";')
        lines.append(f"{indent}  labelloc=t;")
        lines.append(f"{indent}  labeljust=l;")
        lines.extend(_render_node_line(node, indent=f"{indent}  ", options=options))
        rendered.add(node_id)
        for child_id in child_ids:
            _append_node_or_subprocess_cluster(
                lines=lines,
                node_id=child_id,
                nodes_by_id=nodes_by_id,
                children_by_parent=children_by_parent,
                rendered=rendered,
                active_stack=active_stack,
                options=options,
                indent=f"{indent}  ",
            )
        lines.append(f"{indent}}}")
    else:
        lines.extend(_render_node_line(node, indent=indent, options=options))
        rendered.add(node_id)
        for child_id in child_ids:
            _append_node_or_subprocess_cluster(
                lines=lines,
                node_id=child_id,
                nodes_by_id=nodes_by_id,
                children_by_parent=children_by_parent,
                rendered=rendered,
                active_stack=active_stack,
                options=options,
                indent=indent,
            )

    active_stack.remove(node_id)


def _subprocess_parent(node: dict[str, Any]) -> str | None:
    value = node.get("subprocess_parent")
    if value is None:
        return None
    parent_id = str(value).strip()
    return parent_id or None


def _append_edges(
    lines: list[str],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
    boundary_edges: set[tuple[str, str]] | None = None,
    node_sequence_index: dict[str, int] | None = None,
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
            boundary_edges=boundary_edges or set(),
            node_sequence_index=node_sequence_index or {},
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
    boundary_edges: set[tuple[str, str]],
    node_sequence_index: dict[str, int],
) -> list[str]:
    edge_attrs: list[str] = []
    if use_swimlanes and _is_cross_lane_edge(source, target, node_lanes):
        # Keep lane centerlines stable: cross-lane flow should not re-rank lanes.
        edge_attrs.append("constraint=false")

    if (source, target) in boundary_edges:
        edge_attrs.append("minlen=2")
        edge_attrs.append("penwidth=1.2")

    if _is_rework_edge(edge=edge, source=source, target=target, node_sequence_index=node_sequence_index):
        edge_attrs.append("style=dashed")

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


def _is_rework_edge(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    node_sequence_index: dict[str, int],
) -> bool:
    explicit = edge.get("rework")
    if explicit is not None:
        return bool(explicit)

    if str(edge.get("edge_type") or "").strip().lower() == "rework":
        return True

    src_idx = node_sequence_index.get(source)
    dst_idx = node_sequence_index.get(target)
    if src_idx is None or dst_idx is None:
        return False
    return src_idx > dst_idx


def _extract_from_ir_object(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    for node in getattr(process, "nodes", []) or []:
        attrs = getattr(node, "attrs", {}) or {}
        name = attrs.get("name") if isinstance(attrs, dict) else None
        lane = attrs.get("lane") if isinstance(attrs, dict) else None
        note = attrs.get("note") if isinstance(attrs, dict) else None
        subprocess_parent = attrs.get("subprocess_parent") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": name,
                "lane": lane,
                "note": note,
                "subprocess_parent": subprocess_parent,
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
    nodes: list[dict[str, Any]] = []
    for node in nodes_raw:
        if not isinstance(node, dict):
            continue
        node_entry = dict(node)
        attrs = node_entry.get("attrs")
        if "subprocess_parent" not in node_entry and isinstance(attrs, dict):
            parent_id = attrs.get("subprocess_parent")
            if parent_id is not None:
                node_entry["subprocess_parent"] = parent_id
        nodes.append(node_entry)
    edges = [e for e in edges_raw if isinstance(e, dict)]
    return nodes, edges


def _shape_for_kind(kind: str) -> str:
    norm = (kind or "task").lower()
    if norm == "start":
        return "ellipse"
    if norm == "end":
        return "ellipse"
    if norm == "wait":
        return "circle"
    if norm == "decision":
        return "diamond"
    if norm == "subprocess":
        return "component"
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
    if (kind or "").strip().lower() == "subprocess":
        node_attrs.append('style="rounded,filled"')
        node_attrs.append('fillcolor="lightsteelblue1"')
        node_attrs.append("color=steelblue4")
        node_attrs.append("penwidth=1.4")
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
