"""IR assembly helpers for compiler orchestration.

This module owns canonical IR object assembly from normalized adapter data.
"""

from __future__ import annotations

import itertools
from typing import Any

from flo.process.ir.models import Edge, Node

from ._adapter_normalization import normalize_node_attrs, resolve_explicit_transitions


def build_nodes_from_flat_source(flat_source_nodes: list[dict[str, Any]]) -> list[Node]:
    """Build IR nodes from flattened normalized source nodes."""
    nodes: list[Node] = []
    for a_node in flat_source_nodes:
        nid = a_node["id"]
        ntype = a_node["kind"]
        attrs = normalize_node_attrs(a_node)
        subprocess_parent = attrs.pop("subprocess_parent", None)
        nodes.append(
            Node(
                id=nid,
                type=ntype,
                attrs=attrs,
                subprocess_parent=subprocess_parent,
                name=a_node.get("name"),
                description=a_node.get("description"),
                lane=a_node.get("lane"),
                location=a_node.get("location"),
                consumes=a_node.get("consumes") or [],
                produces=a_node.get("produces") or [],
                performed_by=a_node.get("performed_by") or [],
                uses=a_node.get("uses") or [],
                value_class=a_node.get("value_class"),
                cycle_time=a_node.get("cycle_time"),
                wait_time=a_node.get("wait_time"),
                changeover_time=a_node.get("changeover_time"),
                extensions=a_node.get("extensions"),
            )
        )
    return nodes


def build_edges(adapter: dict[str, Any], nodes: list[Node]) -> list[Edge]:
    """Build IR edges from explicit transitions or synthesized outcomes/sequence."""
    explicit_transitions = resolve_explicit_transitions(adapter)
    if isinstance(explicit_transitions, list):
        return _build_explicit_edges(explicit_transitions)

    outcome_edges = _build_named_edges(nodes, "outcomes")
    route_edges = _build_named_edges(nodes, "routes")
    sequential_edges = _build_sequential_edges(nodes)
    return _merge_edges([*outcome_edges, *route_edges], sequential_edges)


def _build_explicit_edges(explicit_edges: list[Any]) -> list[Edge]:
    edges: list[Edge] = []
    for edge in explicit_edges:
        src = edge["source"]
        tgt = edge["target"]
        edges.append(
            Edge(
                source=src,
                target=tgt,
                id=edge.get("id"),
                outcome=_normalize_outcome_value(edge.get("outcome")),
                route=edge.get("route"),
                label=edge.get("label"),
                handoff=edge.get("handoff"),
                rework=edge.get("rework"),
                extensions=edge.get("extensions"),
            )
        )
    return edges


def _build_named_edges(nodes: list[Node], field: str) -> list[Edge]:
    """Assemble model-validated target shorthand and annotated named branches."""
    edges = []
    for node in nodes:
        for name, target in node.attrs.get(field, {}).items():
            spec = {"target": target} if isinstance(target, str) else target
            edges.append(
                Edge(
                    source=node.id,
                    target=spec.get("target", spec.get("to")),
                    outcome=_normalize_outcome_value(name)
                    if field == "outcomes"
                    else None,
                    route=_normalize_outcome_value(name)
                    if field == "routes"
                    else spec.get("route"),
                    **{
                        key: spec.get(key)
                        for key in (
                            "id",
                            "label",
                            "handoff",
                            "rework",
                            "extensions",
                        )
                    },
                )
            )
    return edges


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

    for current, nxt in itertools.pairwise(nodes):
        if current.type == "end":
            continue

        if current.attrs.get("outcomes") or current.attrs.get("routes"):
            # Local branching declarations should not also get
            # an implicit sequential edge.
            continue

        edges.append(Edge(source=current.id, target=nxt.id))

    return edges


def _merge_edges(primary: list[Edge], secondary: list[Edge]) -> list[Edge]:
    merged: list[Edge] = []
    seen: set[tuple[str, str, str | None, str | None]] = set()

    for edge in [*primary, *secondary]:
        key = (edge.source, edge.target, edge.outcome, edge.route)
        if key in seen:
            continue
        seen.add(key)
        merged.append(edge)

    return merged
