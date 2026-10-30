"""Topology-based cycle inspection without inferred rework semantics."""

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from flo.process.graph import GraphFacts
from flo.process.ir.models import IR


@dataclass(frozen=True)
class CycleRegion:
    """One cyclic SCC and detached canonical evidence on its boundaries."""

    node_ids: tuple[str, ...]
    self_loop_node_ids: tuple[str, ...]
    internal_edges: tuple[dict[str, Any], ...]
    entry_edges: tuple[dict[str, Any], ...]
    exit_edges: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        """Return deterministic JSON data detached from both IR and result."""
        return {
            "node_ids": list(self.node_ids),
            "self_loop_node_ids": list(self.self_loop_node_ids),
            "internal_edges": deepcopy(list(self.internal_edges)),
            "entry_edges": deepcopy(list(self.entry_edges)),
            "exit_edges": deepcopy(list(self.exit_edges)),
        }


def analyze_cycles(process: IR) -> tuple[CycleRegion, ...]:
    """Describe maximal cyclic regions, including single-node self-loops."""
    graph = GraphFacts.build((node.id for node in process.nodes), process.edges)
    components = graph.cyclic_components()
    if not components:
        return ()
    membership = {
        node: index for index, nodes in enumerate(components) for node in nodes
    }
    internal: list[list[dict[str, Any]]] = [[] for _ in components]
    entries: list[list[dict[str, Any]]] = [[] for _ in components]
    exits: list[list[dict[str, Any]]] = [[] for _ in components]
    for transition in graph.transitions:
        source = membership.get(transition.source)
        target = membership.get(transition.target)
        if source is None and target is None:
            continue
        edge = asdict(process.edges[transition.key])
        if source is not None and source == target:
            internal[source].append(edge)
        else:
            if source is not None:
                exits[source].append(edge)
            if target is not None:
                entries[target].append(edge)
    return tuple(
        CycleRegion(
            nodes,
            tuple(node for node in nodes if node in graph.successors[node]),
            _ordered(internal[index]),
            _ordered(entries[index]),
            _ordered(exits[index]),
        )
        for index, nodes in enumerate(components)
    )


def _ordered(edges: list[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(sorted(edges, key=lambda edge: json.dumps(edge, sort_keys=True)))
