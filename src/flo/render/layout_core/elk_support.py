"""Private helper logic for FLO's ELK request building."""

from __future__ import annotations

from typing import Any

from .elk_contracts import ElkLayoutEdge, ElkLayoutLane, ElkLayoutNode

_DEFAULT_NODE_WIDTH_PX = 140
_DEFAULT_NODE_HEIGHT_PX = 52


def lane_specs(
    *, process: dict[str, Any] | Any, nodes: list[dict[str, Any]]
) -> tuple[ElkLayoutLane, ...]:
    """Build ordered ELK lane specs from declared lanes and node membership."""
    lane_labels = _declared_lane_labels(process)
    ordered_lane_ids = _ordered_lane_ids(nodes=nodes, lane_labels=lane_labels)

    lanes = _assigned_lanes(
        nodes=nodes,
        ordered_lane_ids=ordered_lane_ids,
        lane_labels=lane_labels,
    )
    unassigned_ids = tuple(
        str(node.get("id") or "")
        for node in nodes
        if not str(node.get("lane") or "").strip() and str(node.get("id") or "")
    )
    if unassigned_ids:
        lanes.append(
            ElkLayoutLane(
                id="unassigned",
                label="unassigned",
                node_ids=unassigned_ids,
            )
        )
    return tuple(lanes)


def ordered_nodes(nodes: list[dict[str, Any]]) -> tuple[ElkLayoutNode, ...]:
    """Convert process nodes into ordered ELK nodes with lane membership."""
    return tuple(_elk_node(node) for node in nodes if str(node.get("id") or ""))


def ordered_flowchart_nodes(nodes: list[dict[str, Any]]) -> tuple[ElkLayoutNode, ...]:
    """Convert process nodes into flowchart ELK nodes without lane assignment."""
    return tuple(
        _elk_node({**node, "lane": None}) for node in nodes if str(node.get("id") or "")
    )


def ordered_edges(edges: list[dict[str, Any]]) -> tuple[ElkLayoutEdge, ...]:
    """Convert process edges into ordered ELK edges."""
    return tuple(
        _elk_edge(edge=edge, index=index)
        for index, edge in enumerate(edges)
        if str(edge.get("source") or "") and str(edge.get("target") or "")
    )


def serialize_node(node: ElkLayoutNode) -> dict[str, Any]:
    """Serialize one ELK node contract into the payload shape ELK expects."""
    out: dict[str, Any] = {
        "id": node.id,
        "width": node.width_px,
        "height": node.height_px,
        "labels": [{"text": node.label}],
    }
    if node.kind:
        out["layoutOptions"] = {"flo.node.kind": node.kind}
    return out


def serialize_edge(edge: ElkLayoutEdge) -> dict[str, Any]:
    """Serialize one ELK edge contract into the payload shape ELK expects."""
    out: dict[str, Any] = {
        "id": edge.id,
        "sources": [edge.source_id],
        "targets": [edge.target_id],
    }
    if edge.label:
        out["labels"] = [{"text": edge.label}]
    return out


def extract_nodes_and_edges(
    process: dict[str, Any] | Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract graph nodes and edges from supported FLO process representations."""
    if process is None:
        return [], []
    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_from_ir_object(process)
    if isinstance(process, dict):
        if isinstance(process.get("nodes"), list):
            return _extract_from_graph_dict(process)
        return _extract_from_adapter_dict(process)
    return [], []


def project_parent_only_subprocess_view(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Hide subprocess parent nodes and reconnect visible edges across them."""
    hidden_ids = {
        str(node.get("id") or "")
        for node in nodes
        if str(node.get("id") or "") and _subprocess_parent(node)
    }
    if not hidden_ids:
        return nodes, edges

    visible_nodes = [
        node
        for node in nodes
        if (node_id := str(node.get("id") or "")) and node_id not in hidden_ids
    ]
    visible_ids = {
        str(node.get("id") or "") for node in visible_nodes if str(node.get("id") or "")
    }
    outgoing = _index_outgoing_edges(edges)
    return visible_nodes, _collapse_hidden_edges(
        visible_ids=visible_ids,
        hidden_ids=hidden_ids,
        outgoing=outgoing,
    )


def edge_label(edge: dict[str, Any]) -> str | None:
    """Return the first non-empty outcome or label text for an edge."""
    for key in ("outcome", "label"):
        value = edge.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _ordered_lane_ids(
    *, nodes: list[dict[str, Any]], lane_labels: dict[str, str]
) -> list[str]:
    ordered_lane_ids = list(lane_labels.keys())
    seen = set(ordered_lane_ids)
    for node in nodes:
        current_lane_id = str(node.get("lane") or "").strip()
        if not current_lane_id or current_lane_id in seen:
            continue
        seen.add(current_lane_id)
        ordered_lane_ids.append(current_lane_id)
        lane_labels[current_lane_id] = current_lane_id
    return ordered_lane_ids


def _assigned_lanes(
    *,
    nodes: list[dict[str, Any]],
    ordered_lane_ids: list[str],
    lane_labels: dict[str, str],
) -> list[ElkLayoutLane]:
    lanes: list[ElkLayoutLane] = []
    for current_lane_id in ordered_lane_ids:
        node_ids = tuple(
            str(node.get("id") or "")
            for node in nodes
            if str(node.get("lane") or "").strip() == current_lane_id
            and str(node.get("id") or "")
        )
        if not node_ids:
            continue
        lanes.append(
            ElkLayoutLane(
                id=current_lane_id,
                label=str(lane_labels.get(current_lane_id) or current_lane_id),
                node_ids=node_ids,
            )
        )
    return lanes


def _declared_lane_labels(process: dict[str, Any] | Any) -> dict[str, str]:
    if not isinstance(process, dict):
        return {}
    raw_lanes = process.get("lanes")
    if not isinstance(raw_lanes, list):
        process_block = process.get("process")
        if isinstance(process_block, dict):
            raw_lanes = process_block.get("lanes")
    if not isinstance(raw_lanes, list):
        return {}

    lane_labels: dict[str, str] = {}
    for raw_lane in raw_lanes:
        if not isinstance(raw_lane, dict):
            continue
        current_lane_id = str(raw_lane.get("id") or "").strip()
        if not current_lane_id:
            continue
        lane_name = (
            str(raw_lane.get("name") or current_lane_id).strip() or current_lane_id
        )
        lane_labels[current_lane_id] = lane_name
    return lane_labels


def _elk_node(node: dict[str, Any]) -> ElkLayoutNode:
    node_id = str(node.get("id") or "")
    return ElkLayoutNode(
        id=node_id,
        label=str(node.get("name") or node_id),
        kind=str(node.get("kind") or ""),
        width_px=_DEFAULT_NODE_WIDTH_PX,
        height_px=_DEFAULT_NODE_HEIGHT_PX,
        lane_id=_lane_id(node),
    )


def _elk_edge(*, edge: dict[str, Any], index: int) -> ElkLayoutEdge:
    source_id = str(edge.get("source") or "")
    target_id = str(edge.get("target") or "")
    return ElkLayoutEdge(
        id=f"e{index}:{source_id}->{target_id}",
        source_id=source_id,
        target_id=target_id,
        label=edge_label(edge),
    )


def _lane_id(node: dict[str, Any]) -> str | None:
    current_lane_id = str(node.get("lane") or "").strip()
    return current_lane_id or None


def _extract_from_ir_object(
    process: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    for node in getattr(process, "nodes", []) or []:
        attrs = getattr(node, "attrs", {}) or {}
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": attrs.get("name") if isinstance(attrs, dict) else None,
                "lane": attrs.get("lane") if isinstance(attrs, dict) else None,
                "note": attrs.get("note") if isinstance(attrs, dict) else None,
                "subprocess_parent": attrs.get("subprocess_parent")
                if isinstance(attrs, dict)
                else None,
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
                "edge_type": getattr(edge, "edge_type", None),
                "rework": getattr(edge, "rework", None),
            }
        )
    return nodes, edges


def _extract_from_graph_dict(
    process: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    for node in process.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_entry = dict(node)
        attrs = node_entry.get("attrs")
        if "subprocess_parent" not in node_entry and isinstance(attrs, dict):
            parent_id = attrs.get("subprocess_parent")
            if parent_id is not None:
                node_entry["subprocess_parent"] = parent_id
        nodes.append(node_entry)
    edges = [edge for edge in (process.get("edges") or []) if isinstance(edge, dict)]
    return nodes, edges


def _extract_from_adapter_dict(
    process: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    steps = process.get("steps")
    transitions = process.get("transitions") or process.get("edges")
    if not isinstance(steps, list):
        if isinstance(transitions, list):
            return [], [edge for edge in transitions if isinstance(edge, dict)]
        return [], []

    nodes: list[dict[str, Any]] = []
    for step in steps:
        _append_step_nodes(nodes, step, parent_id=None)

    if isinstance(transitions, list):
        return nodes, [edge for edge in transitions if isinstance(edge, dict)]
    return nodes, _synthesized_adapter_edges(nodes)


def _append_step_nodes(
    nodes: list[dict[str, Any]], step: Any, *, parent_id: str | None
) -> None:
    if not isinstance(step, dict):
        return
    step_id = str(step.get("id") or "")
    node_entry = dict(step)
    if parent_id is not None and step_id:
        node_entry.setdefault("subprocess_parent", parent_id)
    node_entry.pop("subnodes", None)
    nodes.append(node_entry)
    for subnode in step.get("subnodes") or []:
        _append_step_nodes(nodes, subnode, parent_id=step_id or parent_id)


def _synthesized_adapter_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str | None]] = set()
    for edge in [*_outcome_edges(nodes), *_sequential_edges(nodes)]:
        edge_key = (
            str(edge.get("source") or ""),
            str(edge.get("target") or ""),
            str(edge.get("outcome")) if edge.get("outcome") is not None else None,
        )
        if edge_key in seen:
            continue
        seen.add(edge_key)
        merged.append(edge)
    return merged


def _outcome_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for node in nodes:
        source_id = str(node.get("id") or "")
        outcomes = node.get("outcomes")
        if not source_id or not isinstance(outcomes, dict):
            continue
        for outcome, target_spec in outcomes.items():
            edge = _outcome_edge(
                source_id=source_id, outcome=outcome, target_spec=target_spec
            )
            if edge is not None:
                edges.append(edge)
    return edges


def _outcome_edge(
    *, source_id: str, outcome: Any, target_spec: Any
) -> dict[str, Any] | None:
    if isinstance(target_spec, dict):
        target = target_spec.get("target") or target_spec.get("to")
        if target is None:
            return None
        edge: dict[str, Any] = {
            "source": source_id,
            "target": str(target),
            "outcome": _normalize_outcome_value(outcome),
        }
        for key in ("id", "label", "edge_type", "rework", "metadata"):
            value = target_spec.get(key)
            if value is not None:
                edge[key] = value
        return edge
    if target_spec is None:
        return None
    return {
        "source": source_id,
        "target": str(target_spec),
        "outcome": _normalize_outcome_value(outcome),
    }


def _normalize_outcome_value(value: Any) -> str | None:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return None if value is None else str(value)


def _sequential_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for current, nxt in zip(nodes, nodes[1:]):
        if str(current.get("kind") or "").lower() == "end":
            continue
        outcomes = current.get("outcomes")
        if isinstance(outcomes, dict) and outcomes:
            continue
        source_id = str(current.get("id") or "")
        target_id = str(nxt.get("id") or "")
        if source_id and target_id:
            edges.append({"source": source_id, "target": target_id})
    return edges


def _collapse_hidden_edges(
    *,
    visible_ids: set[str],
    hidden_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    collapsed_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None]] = set()
    for source in visible_ids:
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
        for key in ("outcome", "label", "edge_type", "rework"):
            value = semantic_edge.get(key)
            if value is not None:
                edge[key] = value
        metadata = semantic_edge.get("metadata")
        if isinstance(metadata, dict) and metadata:
            edge["metadata"] = metadata
    if label is not None and "outcome" not in edge and "label" not in edge:
        edge["label"] = label
    collapsed_edges.append(edge)


def _subprocess_parent(node: dict[str, Any]) -> str | None:
    parent_id = node.get("subprocess_parent")
    if parent_id is not None:
        text = str(parent_id).strip()
        if text:
            return text
    metadata = node.get("metadata")
    if not isinstance(metadata, dict):
        return None
    raw_value = metadata.get("subprocess_parent")
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    return text or None
