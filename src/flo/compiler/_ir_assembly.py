"""IR assembly helpers for compiler orchestration.

This module owns canonical IR object assembly from normalized adapter data.
"""

from __future__ import annotations

from typing import Any

from ._adapter_normalization import normalize_node_attrs, resolve_explicit_transitions
from .ir.models import Edge, Node


def build_nodes_from_flat_source(flat_source_nodes: list[dict[str, Any]]) -> list[Node]:
    """Build IR nodes from flattened normalized source nodes."""
    nodes: list[Node] = []
    for idx, a_node in enumerate(flat_source_nodes):
        if not isinstance(a_node, dict):
            continue
        nid = a_node.get("id") or f"n{idx}"
        ntype = a_node.get("kind") or a_node.get("type") or "task"
        attrs = normalize_node_attrs(a_node)
        nodes.append(Node(id=str(nid), type=str(ntype), attrs=attrs))
    return nodes


def build_edges(adapter: dict[str, Any], nodes: list[Node]) -> list[Edge]:
    """Build IR edges from explicit transitions or synthesized outcomes/sequence."""
    explicit_transitions = resolve_explicit_transitions(adapter)
    if isinstance(explicit_transitions, list):
        return _build_explicit_edges(explicit_transitions)

    outcome_edges = _build_outcome_edges(nodes)
    sequential_edges = _build_sequential_edges(nodes)
    return _merge_edges(outcome_edges, sequential_edges)


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
                outcome=_normalize_outcome_value(edge.get("outcome")),
                label=str(edge.get("label")) if edge.get("label") is not None else None,
                edge_type=str(edge.get("edge_type"))
                if edge.get("edge_type") is not None
                else None,
                rework=edge.get("rework")
                if isinstance(edge.get("rework"), bool)
                else None,
                metadata=edge.get("metadata")
                if isinstance(edge.get("metadata"), dict)
                else None,
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
            outcome_edge = _build_outcome_edge(
                source=node.id, outcome=outcome, target_spec=target
            )
            if outcome_edge is not None:
                edges.append(outcome_edge)
    return edges


def _build_outcome_edge(*, source: str, outcome: Any, target_spec: Any) -> Edge | None:
    if isinstance(target_spec, dict):
        target = target_spec.get("target")
        if target is None:
            target = target_spec.get("to")
        if target is None:
            return None
        return Edge(
            source=source,
            target=str(target),
            outcome=_normalize_outcome_value(outcome),
            id=str(target_spec.get("id"))
            if target_spec.get("id") is not None
            else None,
            label=str(target_spec.get("label"))
            if target_spec.get("label") is not None
            else None,
            edge_type=str(target_spec.get("edge_type"))
            if target_spec.get("edge_type") is not None
            else None,
            rework=target_spec.get("rework")
            if isinstance(target_spec.get("rework"), bool)
            else None,
            metadata=target_spec.get("metadata")
            if isinstance(target_spec.get("metadata"), dict)
            else None,
        )

    if target_spec is None:
        return None
    return Edge(
        source=source,
        target=str(target_spec),
        outcome=_normalize_outcome_value(outcome),
    )


def _normalize_outcome_value(value: Any) -> str | None:
    if value is None:
        return None
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value)


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
