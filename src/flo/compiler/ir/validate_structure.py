"""Validation helpers for structural graph constraints in FLO IR."""

from __future__ import annotations

from typing import Any

from .models import IR
from flo.errors import ValidationError


def validate_parallel_structure(
    obj: IR,
    incoming_counts: dict[str, int],
    outgoing_counts: dict[str, int],
) -> None:
    """Validate structural constraints for explicit parallel split/join nodes."""
    split_ids = [
        node.id for node in obj.nodes if (node.type or "").lower() == "parallel_split"
    ]
    join_ids = {
        node.id for node in obj.nodes if (node.type or "").lower() == "parallel_join"
    }

    if not split_ids and not join_ids:
        return

    node_ids = [node.id for node in obj.nodes]
    adjacency, reverse_adjacency = _build_adjacency_maps(
        node_ids=node_ids, edges=obj.edges
    )

    _validate_parallel_splits(
        split_ids=split_ids,
        join_ids=join_ids,
        outgoing_counts=outgoing_counts,
        adjacency=adjacency,
    )
    _validate_parallel_joins(
        split_ids=split_ids,
        join_ids=join_ids,
        incoming_counts=incoming_counts,
        reverse_adjacency=reverse_adjacency,
    )


def _validate_parallel_splits(
    *,
    split_ids: list[str],
    join_ids: set[str],
    outgoing_counts: dict[str, int],
    adjacency: dict[str, set[str]],
) -> None:
    for split_id in split_ids:
        if outgoing_counts.get(split_id, 0) < 2:
            raise ValidationError(
                f"E1011: parallel_split node '{split_id}' must have at least two outgoing edges"
            )

        reachable_from_split = _traverse([split_id], adjacency)
        if not any(candidate in join_ids for candidate in reachable_from_split):
            raise ValidationError(
                f"E1012: parallel_split node '{split_id}' must reach at least one parallel_join node"
            )


def _validate_parallel_joins(
    *,
    split_ids: list[str],
    join_ids: set[str],
    incoming_counts: dict[str, int],
    reverse_adjacency: dict[str, set[str]],
) -> None:
    for join_id in join_ids:
        if incoming_counts.get(join_id, 0) < 2:
            raise ValidationError(
                f"E1013: parallel_join node '{join_id}' must have at least two incoming edges"
            )

        upstream_for_join = _traverse([join_id], reverse_adjacency)
        if not any(candidate in split_ids for candidate in upstream_for_join):
            raise ValidationError(
                f"E1014: parallel_join node '{join_id}' must be reachable from at least one parallel_split node"
            )


def _build_adjacency_maps(
    node_ids: list[str],
    edges: list[Any],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    id_set = set(node_ids)
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}
    reverse_adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}

    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            reverse_adjacency[edge.target].add(edge.source)

    return adjacency, reverse_adjacency


def _traverse(seed_ids: list[str], graph: dict[str, set[str]]) -> set[str]:
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
