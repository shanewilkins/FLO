"""Shared graph traversal helpers for IR validation modules."""

from __future__ import annotations

from typing import Any


def build_adjacency_maps(
    node_ids: list[str],
    edges: list[Any],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build forward and reverse adjacency maps from validated edge references."""
    id_set = set(node_ids)
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}
    reverse_adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}

    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            reverse_adjacency[edge.target].add(edge.source)

    return adjacency, reverse_adjacency


def traverse(seed_ids: list[str], graph: dict[str, set[str]]) -> set[str]:
    """Return all nodes reachable from the provided seed ids in a graph."""
    visited: set[str] = set()
    stack: list[str] = list(seed_ids)
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for nxt in graph.get(current, set()):
            if nxt not in visited:
                stack.append(nxt)
    return visited
