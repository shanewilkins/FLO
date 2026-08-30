"""Deterministic graph primitives shared by canonical IR analyses."""

from __future__ import annotations

from collections.abc import Iterable

from flo.process.ir.models import Edge, IR


def build_adjacency(
    process: IR, *, edges: Iterable[Edge] | None = None
) -> dict[str, tuple[str, ...]]:
    """Return sorted, duplicate-free adjacency for declared process nodes."""
    targets: dict[str, set[str]] = {node.id: set() for node in process.nodes}
    for edge in process.edges if edges is None else edges:
        if edge.source in targets and edge.target in targets:
            targets[edge.source].add(edge.target)
    return {
        node_id: tuple(sorted(node_targets))
        for node_id, node_targets in sorted(targets.items())
    }


def has_cycle(adjacency: dict[str, tuple[str, ...]]) -> bool:
    """Return whether the directed adjacency contains a cycle."""
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in active:
            return True
        if node_id in visited:
            return False
        active.add(node_id)
        if any(visit(target_id) for target_id in adjacency.get(node_id, ())):
            return True
        active.remove(node_id)
        visited.add(node_id)
        return False

    return any(
        visit(node_id) for node_id in sorted(adjacency) if node_id not in visited
    )


def enumerate_paths(
    *,
    start_id: str,
    end_ids: set[str],
    adjacency: dict[str, tuple[str, ...]],
    limit: int,
) -> tuple[tuple[tuple[str, ...], ...], bool]:
    """Enumerate sorted start-to-end paths, reporting deterministic truncation."""
    paths: list[tuple[str, ...]] = []
    stack: list[tuple[str, tuple[str, ...]]] = [(start_id, (start_id,))]
    while stack:
        node_id, path = stack.pop()
        if node_id in end_ids:
            paths.append(path)
            if len(paths) > limit:
                return (), True
            continue
        for target_id in reversed(adjacency.get(node_id, ())):
            stack.append((target_id, (*path, target_id)))
    return tuple(paths), False
