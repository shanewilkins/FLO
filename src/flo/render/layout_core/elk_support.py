"""Private helper logic for FLO's ELK request building."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flo.process.ir.models import IR
from flo.process.ir.schema_projection import ir_to_schema_dict
from flo.render.options import RenderOptions

from .elk_contracts import ElkLayoutEdge, ElkLayoutNode, ElkSerialization
from .rework_semantics import resolve_rework_route_variant

_DEFAULT_NODE_WIDTH_PX = 140
_DEFAULT_NODE_HEIGHT_PX = 52

NodeSizeResolver = Callable[[dict[str, Any], RenderOptions], tuple[int, int]]
EdgeDecorator = Callable[[ElkLayoutEdge, dict[str, Any]], ElkLayoutEdge]


def ordered_nodes(
    nodes: list[dict[str, Any]],
    *,
    options: RenderOptions | None = None,
    size_resolver: NodeSizeResolver | None = None,
) -> tuple[ElkLayoutNode, ...]:
    """Convert process nodes into ordered ELK nodes with lane membership."""
    return tuple(
        _elk_node(
            node,
            options=options,
            size_resolver=size_resolver,
            partition_index=index,
        )
        for index, node in enumerate(nodes)
        if str(node.get("id") or "")
    )


def ordered_edges(
    edges: list[dict[str, Any]],
    *,
    node_kinds: dict[str, str] | None = None,
    decorator: EdgeDecorator | None = None,
) -> tuple[ElkLayoutEdge, ...]:
    """Convert process edges into ordered ELK edges."""
    return tuple(
        _elk_edge(
            edge=edge,
            index=index,
            node_kinds=node_kinds or {},
            decorator=decorator,
        )
        for index, edge in enumerate(edges)
        if str(edge.get("source") or "") and str(edge.get("target") or "")
    )


def serialize_node(
    node: ElkLayoutNode,
    *,
    constrain_terminal_layers: bool = True,
    settings: ElkSerialization | None = None,
) -> dict[str, Any]:
    """Serialize one ELK node contract into the payload shape ELK expects."""
    out: dict[str, Any] = {
        "id": node.id,
        "width": node.width_px,
        "height": node.height_px,
        "labels": [{"text": node.label}],
    }
    layout_options: dict[str, str] = {}
    if node.kind:
        layout_options["flo.node.kind"] = node.kind
    if node.kind == "start" and constrain_terminal_layers:
        layout_options["elk.layered.layering.layerConstraint"] = "FIRST"
    elif node.kind == "end" and constrain_terminal_layers:
        layout_options["elk.layered.layering.layerConstraint"] = "LAST"
    if node.partition_index is not None:
        layout_options["elk.partitioning.partition"] = str(node.partition_index)
    if layout_options:
        out["layoutOptions"] = layout_options
    if settings is not None:
        extras = settings.node_overrides.get(node.id, {})
        layout_options.update(extras.get("layoutOptions", {}))
        if "ports" in extras:
            out["ports"] = extras["ports"]
        if layout_options:
            out["layoutOptions"] = layout_options
    return out


def serialize_edge(
    edge: ElkLayoutEdge, *, settings: ElkSerialization | None = None
) -> dict[str, Any]:
    """Serialize one ELK edge contract into the payload shape ELK expects."""
    source_endpoint = edge.source_id
    target_endpoint = edge.target_id
    out: dict[str, Any] = {
        "id": edge.id,
        "sources": [source_endpoint],
        "targets": [target_endpoint],
    }
    if edge.label and (settings is None or edge.id not in settings.unlabeled_edge_ids):
        out["labels"] = [{"text": edge.label}]
    if settings is not None:
        out.update(settings.edge_overrides.get(edge.id, {}))
    return out


def extract_nodes_and_edges(
    process: dict[str, Any] | Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract graph nodes and edges from supported FLO process representations."""
    if process is None:
        return [], []
    if isinstance(process, IR):
        graph = ir_to_schema_dict(process)
        return graph["nodes"], graph["edges"]
    if isinstance(process, dict):
        if isinstance(process.get("nodes"), list):
            return _extract_from_graph_dict(process)
        raise TypeError("layout requires compiled IR or canonical nodes/edges")
    return [], []


def project_parent_only_subprocess_view(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Hide subprocess parent nodes and reconnect visible edges across them."""
    hidden_ids = _hidden_subprocess_parent_ids(nodes)
    if not hidden_ids:
        return nodes, edges

    visible_nodes = _visible_non_hidden_nodes(nodes, hidden_ids=hidden_ids)
    visible_ids = _node_ids(visible_nodes)
    outgoing = _index_outgoing_edges(edges)
    visible_order = _node_id_order(visible_nodes)
    return visible_nodes, _collapse_hidden_edges(
        visible_order=visible_order,
        visible_ids=visible_ids,
        hidden_ids=hidden_ids,
        outgoing=outgoing,
    )


def _hidden_subprocess_parent_ids(nodes: list[dict[str, Any]]) -> set[str]:
    return {
        node_id
        for node in nodes
        if (node_id := str(node.get("id") or "")) and _subprocess_parent(node)
    }


def _visible_non_hidden_nodes(
    nodes: list[dict[str, Any]], *, hidden_ids: set[str]
) -> list[dict[str, Any]]:
    return [
        node
        for node in nodes
        if (node_id := str(node.get("id") or "")) and node_id not in hidden_ids
    ]


def _node_ids(nodes: list[dict[str, Any]]) -> set[str]:
    return {node_id for node in nodes if (node_id := str(node.get("id") or ""))}


def _node_id_order(nodes: list[dict[str, Any]]) -> list[str]:
    return [node_id for node in nodes if (node_id := str(node.get("id") or ""))]


def edge_label(edge: dict[str, Any]) -> str | None:
    """Return explicit display text, falling back to the semantic outcome."""
    for key in ("label", "outcome"):
        value = edge.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _elk_node(
    node: dict[str, Any],
    *,
    options: RenderOptions | None = None,
    size_resolver: NodeSizeResolver | None = None,
    partition_index: int | None = None,
) -> ElkLayoutNode:
    node_id = str(node.get("id") or "")
    width_px = _DEFAULT_NODE_WIDTH_PX
    height_px = _DEFAULT_NODE_HEIGHT_PX
    if size_resolver is not None and options is not None:
        width_px, height_px = size_resolver(node, options)
    elif options is not None:
        scale = options.resolved_theme.typography_scale
        width_px = round(width_px * scale)
        height_px = round(height_px * scale)
    return ElkLayoutNode(
        id=node_id,
        label=str(node.get("name") or node_id),
        kind=str(node.get("kind") or ""),
        width_px=width_px,
        height_px=height_px,
        lane_id=_lane_id(node),
        partition_index=partition_index,
    )


def _elk_edge(
    *,
    edge: dict[str, Any],
    index: int,
    node_kinds: dict[str, str],
    decorator: EdgeDecorator | None = None,
) -> ElkLayoutEdge:
    source_id = str(edge.get("source") or "")
    target_id = str(edge.get("target") or "")
    label = edge_label(edge)
    source_kind = str(node_kinds.get(source_id) or "task")
    rework_variant = resolve_rework_route_variant(edge, source_kind=source_kind)
    source_port_side: str | None = None
    target_port_side: str | None = None
    layout_edge = ElkLayoutEdge(
        id=f"e{index}:{source_id}->{target_id}",
        source_id=source_id,
        target_id=target_id,
        label=label,
        is_rework=rework_variant is not None,
        rework_variant=rework_variant,
        source_port_side=source_port_side,
        target_port_side=target_port_side,
    )
    return decorator(layout_edge, edge) if decorator is not None else layout_edge


def _lane_id(node: dict[str, Any]) -> str | None:
    current_lane_id = str(node.get("lane") or "").strip()
    return current_lane_id or None


def _extract_from_graph_dict(
    process: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return list(process["nodes"]), list(process.get("edges", []))


def _collapse_hidden_edges(
    *,
    visible_order: list[str],
    visible_ids: set[str],
    hidden_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    collapsed_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None]] = set()
    for source in visible_order:
        for edge in outgoing.get(source, []):
            _append_visible_or_nested_edges(
                source=source,
                edge=edge,
                visible_ids=visible_ids,
                hidden_ids=hidden_ids,
                outgoing=outgoing,
                collapsed_edges=collapsed_edges,
                seen_edges=seen_edges,
            )
    return collapsed_edges


def _append_visible_or_nested_edges(
    *,
    source: str,
    edge: dict[str, Any],
    visible_ids: set[str],
    hidden_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
    collapsed_edges: list[dict[str, Any]],
    seen_edges: set[tuple[str, str, str | None]],
) -> None:
    target = str(edge.get("target") or "")
    if not target:
        return
    label = edge_label(edge)
    if target in visible_ids:
        _append_collapsed_edge(
            collapsed_edges=collapsed_edges,
            seen_edges=seen_edges,
            source=source,
            target=target,
            label=label,
            semantic_edge=edge,
        )
        return
    if target not in hidden_ids:
        return
    for nested_target, next_label, semantic_edge in _visible_targets_through_hidden(
        start_hidden=target,
        hidden_ids=hidden_ids,
        visible_ids=visible_ids,
        outgoing=outgoing,
        active_label=label,
        active_edge=edge,
    ):
        _append_collapsed_edge(
            collapsed_edges=collapsed_edges,
            seen_edges=seen_edges,
            source=source,
            target=nested_target,
            label=next_label,
            semantic_edge=semantic_edge,
        )


def _index_outgoing_edges(
    edges: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source and target:
            outgoing.setdefault(source, []).append(edge)
    return outgoing


def _visible_targets_through_hidden(
    *,
    start_hidden: str,
    hidden_ids: set[str],
    visible_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
    active_label: str | None,
    active_edge: dict[str, Any] | None,
) -> list[tuple[str, str | None, dict[str, Any] | None]]:
    targets: list[tuple[str, str | None, dict[str, Any] | None]] = []
    pending: list[tuple[str, str | None, dict[str, Any] | None]] = [
        (start_hidden, active_label, active_edge)
    ]
    visited_hidden: set[tuple[str, str | None]] = set()
    while pending:
        hidden_id, current_label, current_edge = pending.pop()
        state = (hidden_id, current_label)
        if state in visited_hidden:
            continue
        visited_hidden.add(state)
        for edge in outgoing.get(hidden_id, []):
            target = str(edge.get("target") or "")
            if not target:
                continue
            next_label = edge_label(edge) or current_label
            semantic_edge = edge if current_edge is None else current_edge
            if target in visible_ids:
                targets.append((target, next_label, semantic_edge))
            elif target in hidden_ids:
                pending.append((target, next_label, semantic_edge))
    return targets


def _append_collapsed_edge(
    *,
    collapsed_edges: list[dict[str, Any]],
    seen_edges: set[tuple[str, str, str | None]],
    source: str,
    target: str,
    label: str | None,
    semantic_edge: dict[str, Any] | None,
) -> None:
    if source == target:
        return
    edge_key = (source, target, label)
    if edge_key in seen_edges:
        return
    seen_edges.add(edge_key)

    edge: dict[str, Any] = {"source": source, "target": target}
    if isinstance(semantic_edge, dict):
        for key in ("outcome", "label", "handoff", "rework", "extensions"):
            value = semantic_edge.get(key)
            if value is not None:
                edge[key] = value
    if label is not None and "outcome" not in edge and "label" not in edge:
        edge["label"] = label
    collapsed_edges.append(edge)


def _subprocess_parent(node: dict[str, Any]) -> str | None:
    parent_id = node.get("subprocess_parent")
    if parent_id is not None:
        text = str(parent_id).strip()
        if text:
            return text
    return None
