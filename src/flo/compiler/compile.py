"""Compiler stub: adapter -> IR conversion.

The real compiler will convert adapter models into the canonical
FlowProcess IR (instances of `flo.ir.models.FlowProcess`). This stub
is a placeholder that will be implemented as part of v0.1.
"""
from typing import Any, Dict

from .ir.models import IR, Node, Edge


def compile_adapter(adapter_model: Dict[str, Any]) -> IR:
    """Compile an adapter model into a minimal canonical `IR` instance.

    This is a tiny, pragmatic implementation used by the test harness
    to validate wiring; real compilation logic will replace this.
    """
    adapter = adapter_model or {}
    name = _resolve_process_name(adapter)
    process_metadata = _resolve_process_metadata(adapter)
    source_nodes = _resolve_source_nodes(adapter)

    if not isinstance(source_nodes, list):
        fallback_node = Node(id="n1", type="task", attrs={"name": name})
        return IR(name=name, nodes=[fallback_node], edges=[], process_metadata=process_metadata)

    nodes = _build_nodes(source_nodes)
    edges = _build_edges(adapter=adapter, nodes=nodes)
    return IR(name=name, nodes=nodes, edges=edges, process_metadata=process_metadata)


def _resolve_process_name(adapter: dict[str, Any]) -> str:
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}
    return str(process.get("id") or process.get("name") or adapter.get("name") or "unnamed")


def _resolve_process_metadata(adapter: dict[str, Any]) -> dict[str, Any] | None:
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}

    metadata_raw = process.get("metadata")
    metadata: dict[str, Any] = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}

    for key in ("materials", "equipment", "locations", "workers"):
        value = adapter.get(key)
        if not _is_resource_collection(value):
            value = process.get(key)
        if _is_resource_collection(value):
            metadata[key] = value

    return metadata or None


def _is_resource_collection(value: Any) -> bool:
    if isinstance(value, list):
        return True
    if not isinstance(value, dict):
        return False

    has_nested_collection = False
    for group_name, group_value in value.items():
        if not isinstance(group_name, str) or not group_name.strip():
            return False

        if group_name == "name":
            if not isinstance(group_value, str) or not group_value.strip():
                return False
            continue

        if not isinstance(group_value, (list, dict)):
            return False
        has_nested_collection = True

    return has_nested_collection


def _resolve_source_nodes(adapter: dict[str, Any]) -> Any:
    steps = adapter.get("steps")
    if isinstance(steps, list):
        return steps
    return adapter.get("nodes")


def _build_nodes(source_nodes: list[Any]) -> list[Node]:
    nodes: list[Node] = []
    for idx, a_node in enumerate(source_nodes):
        if not isinstance(a_node, dict):
            continue
        nid = a_node.get("id") or f"n{idx}"
        ntype = a_node.get("kind") or a_node.get("type") or "task"
        attrs = _normalize_node_attrs(a_node)
        nodes.append(Node(id=str(nid), type=str(ntype), attrs=attrs))
    return nodes


def _normalize_node_attrs(a_node: dict[str, Any]) -> dict[str, Any]:
    attrs = a_node.get("attrs")
    if isinstance(attrs, dict):
        return attrs

    normalized: dict[str, Any] = {}
    for key in ("name", "lane", "note", "metadata", "inputs", "outputs"):
        if key in a_node:
            normalized[key] = a_node[key]
    outcomes = a_node.get("outcomes")
    if isinstance(outcomes, dict):
        normalized["outcomes"] = outcomes
    return normalized


def _build_edges(adapter: dict[str, Any], nodes: list[Node]) -> list[Edge]:
    explicit_transitions = _resolve_explicit_transitions(adapter)
    if isinstance(explicit_transitions, list):
        return _build_explicit_edges(explicit_transitions)

    outcome_edges = _build_outcome_edges(nodes)
    sequential_edges = _build_sequential_edges(nodes)
    return _merge_edges(outcome_edges, sequential_edges)


def _resolve_explicit_transitions(adapter: dict[str, Any]) -> Any:
    transitions = adapter.get("transitions")
    if isinstance(transitions, list):
        return transitions

    return adapter.get("edges")


def _build_explicit_edges(explicit_edges: list[Any]) -> list[Edge]:
    edges: list[Edge] = []
    for edge in explicit_edges:
        if not isinstance(edge, dict):
            continue
        src = edge.get("source")
        if src is None:
            src = edge.get("from")
        tgt = edge.get("target")
        if tgt is None:
            tgt = edge.get("to")
        if src is None or tgt is None:
            continue
        edges.append(
            Edge(
                source=str(src),
                target=str(tgt),
                id=str(edge.get("id")) if edge.get("id") is not None else None,
                outcome=str(edge.get("outcome")) if edge.get("outcome") is not None else None,
                label=str(edge.get("label")) if edge.get("label") is not None else None,
                metadata=edge.get("metadata") if isinstance(edge.get("metadata"), dict) else None,
            )
        )
    return edges


def _build_outcome_edges(nodes: list[Node]) -> list[Edge]:
    edges: list[Edge] = []
    for node in nodes:
        attrs = node.attrs or {}
        outcomes = attrs.get("outcomes") if isinstance(attrs, dict) else None
        if not isinstance(outcomes, dict):
            continue
        for outcome, target in outcomes.items():
            edges.append(Edge(source=node.id, target=str(target), outcome=str(outcome)))
    return edges


def _build_sequential_edges(nodes: list[Node]) -> list[Edge]:
    edges: list[Edge] = []
    if len(nodes) < 2:
        return edges

    for current, nxt in zip(nodes, nodes[1:]):
        current_type = (current.type or "").lower()
        if current_type == "end":
            continue

        attrs = current.attrs or {}
        outcomes = attrs.get("outcomes") if isinstance(attrs, dict) else None
        if isinstance(outcomes, dict) and outcomes:
            # Decision-like nodes with explicit outcomes should not also get
            # an implicit sequential edge.
            continue

        edges.append(Edge(source=current.id, target=nxt.id))

    return edges


def _merge_edges(primary: list[Edge], secondary: list[Edge]) -> list[Edge]:
    merged: list[Edge] = []
    seen: set[tuple[str, str, str | None]] = set()

    for edge in [*primary, *secondary]:
        key = (edge.source, edge.target, edge.outcome)
        if key in seen:
            continue
        seen.add(key)
        merged.append(edge)

    return merged
