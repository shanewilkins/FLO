"""Read-only topology facts over canonical transition identities."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol

import networkx as nx


class DirectedTransition(Protocol):
    """Endpoint interface that keeps graph facts independent of IR packages."""

    source: str
    target: str


@dataclass(frozen=True)
class GraphTransition:
    """A unique ordinal mapping to an original canonical transition."""

    key: int
    source: str
    target: str


@dataclass(frozen=True)
class GraphFacts:
    """Separate transition multiplicity from distinct-neighbor topology."""

    transitions: tuple[GraphTransition, ...]
    successors: Mapping[str, tuple[str, ...]]
    predecessors: Mapping[str, tuple[str, ...]]
    incoming_records: Mapping[str, int]
    outgoing_records: Mapping[str, int]
    _topology: nx.MultiDiGraph = field(repr=False, compare=False)

    @classmethod
    def build(
        cls, node_ids: Iterable[str], edges: Iterable[DirectedTransition]
    ) -> GraphFacts:
        """Snapshot resolved endpoints without copying or rewriting evidence."""
        topology = nx.MultiDiGraph()
        topology.add_nodes_from(sorted(node_ids))
        transitions = []
        for key, edge in enumerate(edges):
            if edge.source not in topology or edge.target not in topology:
                raise ValueError(
                    f"Graph endpoint unresolved: {edge.source} -> {edge.target}"
                )
            transitions.append(GraphTransition(key, edge.source, edge.target))
            topology.add_edge(edge.source, edge.target, key=key)
        return cls(
            tuple(transitions),
            MappingProxyType(
                {node: tuple(sorted(topology.successors(node))) for node in topology}
            ),
            MappingProxyType(
                {node: tuple(sorted(topology.predecessors(node))) for node in topology}
            ),
            MappingProxyType(dict(topology.in_degree)),
            MappingProxyType(dict(topology.out_degree)),
            nx.freeze(topology),
        )

    def components(self) -> tuple[tuple[str, ...], ...]:
        """Return deterministic SCCs using NetworkX's iterative implementation."""
        return tuple(
            sorted(
                tuple(sorted(members))
                for members in nx.strongly_connected_components(self._topology)
            )
        )

    def reachable(self, seeds: Iterable[str], *, reverse: bool = False) -> set[str]:
        """Return multi-source reachability without recursion or graph mutation."""
        graph = self._topology.reverse(copy=False) if reverse else self._topology
        sources = list(seeds)
        if not sources:
            return set()
        return {node for layer in nx.bfs_layers(graph, sources) for node in layer}

    def cyclic_components(self) -> tuple[tuple[str, ...], ...]:
        """Include nontrivial SCCs and single-node self-loops."""
        return tuple(
            members
            for members in self.components()
            if len(members) > 1 or members[0] in self.successors[members[0]]
        )
