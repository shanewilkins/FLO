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
    source_nodes = _resolve_source_nodes(adapter)

    if not isinstance(source_nodes, list):
        fallback_node = Node(id="n1", type="task", attrs={"name": name})
        return IR(name=name, nodes=[fallback_node], edges=[])

    nodes = _build_nodes(source_nodes)
    edges = _build_edges(adapter=adapter, nodes=nodes)
    return IR(name=name, nodes=nodes, edges=edges)


def _resolve_process_name(adapter: dict[str, Any]) -> str:
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}
    return str(process.get("id") or process.get("name") or adapter.get("name") or "unnamed")


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
    for key in ("name", "lane", "metadata"):
        if key in a_node:
            normalized[key] = a_node[key]
    outcomes = a_node.get("outcomes")
    if isinstance(outcomes, dict):
        normalized["outcomes"] = outcomes
    return normalized


def _build_edges(adapter: dict[str, Any], nodes: list[Node]) -> list[Edge]:
    explicit_edges = adapter.get("edges")
    if isinstance(explicit_edges, list):
        return _build_explicit_edges(explicit_edges)
    return _build_outcome_edges(nodes)


def _build_explicit_edges(explicit_edges: list[Any]) -> list[Edge]:
    edges: list[Edge] = []
    for edge in explicit_edges:
        if not isinstance(edge, dict):
            continue
        src = edge.get("source")
        tgt = edge.get("target")
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
