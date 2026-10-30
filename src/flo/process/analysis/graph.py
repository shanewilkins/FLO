"""Deterministic graph primitives shared by canonical IR analyses."""

from __future__ import annotations

from collections.abc import Mapping


def enumerate_paths(
    *,
    start_id: str,
    end_ids: set[str],
    adjacency: Mapping[str, tuple[str, ...]],
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
