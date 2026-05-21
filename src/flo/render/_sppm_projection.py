"""SPPM-specific subprocess projection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._graphviz_dot_common import (
    _project_parent_only_subprocess_view,
    _project_subprocess_visible_ids,
)
from .options import RenderOptions


@dataclass(frozen=True)
class SppmProjectionContext:
    """Resolved SPPM projection metadata for publication and diagnostics."""

    requested_mode: str
    effective_mode: str
    focus_subprocess: str | None = None
    parent_subprocess: str | None = None
    entry_context: tuple[str, ...] = ()
    exit_context: tuple[str, ...] = ()
    fallback_reason: str | None = None


def project_sppm_subprocess_view(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    options: RenderOptions,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SppmProjectionContext]:
    """Return projected SPPM nodes, edges, and effective projection metadata."""
    requested_mode = options.sppm_projection
    focus_id = _normalize_focus_id(options.sppm_focus_subprocess)
    nodes_by_id = _nodes_by_id(nodes)

    if requested_mode == "child_map":
        return _project_child_map(
            nodes,
            edges,
            nodes_by_id=nodes_by_id,
            focus_id=focus_id,
            requested_mode=requested_mode,
        )
    if requested_mode == "inline":
        return _project_inline(
            nodes, edges, nodes_by_id=nodes_by_id, focus_id=focus_id, options=options
        )
    projected_nodes, projected_edges = _project_parent_only_subprocess_view(
        nodes, edges
    )
    return (
        projected_nodes,
        projected_edges,
        SppmProjectionContext(
            requested_mode=requested_mode,
            effective_mode="top_level",
        ),
    )


def _project_child_map(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    nodes_by_id: dict[str, dict[str, Any]],
    focus_id: str | None,
    requested_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SppmProjectionContext]:
    if not _is_subprocess_node(focus_id, nodes_by_id):
        projected_nodes, projected_edges = _project_parent_only_subprocess_view(
            nodes, edges
        )
        return (
            projected_nodes,
            projected_edges,
            SppmProjectionContext(
                requested_mode=requested_mode,
                effective_mode="top_level",
                fallback_reason="missing-focus-subprocess",
            ),
        )
    assert focus_id is not None

    descendant_ids = _descendant_ids(focus_id, nodes_by_id=nodes_by_id)
    subtree_ids = {focus_id, *descendant_ids}
    entry_ids = _incoming_neighbor_ids(subtree_ids, edges)
    exit_ids = _outgoing_neighbor_ids(subtree_ids, edges)
    visible_ids = subtree_ids | entry_ids | exit_ids
    projected_nodes, projected_edges = _project_subprocess_visible_ids(
        nodes, edges, visible_ids=visible_ids
    )

    parent_subprocess = _subprocess_parent(nodes_by_id.get(focus_id, {}))
    return (
        projected_nodes,
        projected_edges,
        SppmProjectionContext(
            requested_mode=requested_mode,
            effective_mode="child_map",
            focus_subprocess=focus_id,
            parent_subprocess=parent_subprocess,
            entry_context=tuple(sorted(entry_ids)),
            exit_context=tuple(sorted(exit_ids)),
        ),
    )


def _project_inline(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    nodes_by_id: dict[str, dict[str, Any]],
    focus_id: str | None,
    options: RenderOptions,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], SppmProjectionContext]:
    if not _is_subprocess_node(focus_id, nodes_by_id):
        projected_nodes, projected_edges = _project_parent_only_subprocess_view(
            nodes, edges
        )
        return (
            projected_nodes,
            projected_edges,
            SppmProjectionContext(
                requested_mode="inline",
                effective_mode="top_level",
                fallback_reason="missing-focus-subprocess",
            ),
        )
    assert focus_id is not None

    descendant_ids = _descendant_ids(focus_id, nodes_by_id=nodes_by_id)
    if len(descendant_ids) > _inline_budget(options):
        projected_nodes, projected_edges, context = _project_child_map(
            nodes,
            edges,
            nodes_by_id=nodes_by_id,
            focus_id=focus_id,
            requested_mode="inline",
        )
        return (
            projected_nodes,
            projected_edges,
            SppmProjectionContext(
                requested_mode="inline",
                effective_mode=context.effective_mode,
                focus_subprocess=context.focus_subprocess,
                parent_subprocess=context.parent_subprocess,
                entry_context=context.entry_context,
                exit_context=context.exit_context,
                fallback_reason="inline-budget-exceeded",
            ),
        )

    top_level_ids = {
        node_id
        for node_id, node in nodes_by_id.items()
        if _subprocess_parent(node) is None
    }
    visible_ids = top_level_ids | descendant_ids
    projected_nodes, projected_edges = _project_subprocess_visible_ids(
        nodes, edges, visible_ids=visible_ids
    )
    return (
        projected_nodes,
        projected_edges,
        SppmProjectionContext(
            requested_mode="inline",
            effective_mode="inline",
            focus_subprocess=focus_id,
            parent_subprocess=_subprocess_parent(nodes_by_id.get(focus_id, {})),
        ),
    )


def _inline_budget(options: RenderOptions) -> int:
    base = options.layout_target_columns or 4
    if options.layout_fit == "fit-strict":
        return max(2, min(6, base - 1))
    return max(3, min(8, base))


def _nodes_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id") or ""): node for node in nodes if node.get("id")}


def _descendant_ids(
    focus_id: str, *, nodes_by_id: dict[str, dict[str, Any]]
) -> set[str]:
    descendants: set[str] = set()
    pending = [focus_id]
    while pending:
        current = pending.pop()
        for node_id, node in nodes_by_id.items():
            if node_id in descendants or node_id == focus_id:
                continue
            if _subprocess_parent(node) != current:
                continue
            descendants.add(node_id)
            pending.append(node_id)
    return descendants


def _incoming_neighbor_ids(
    visible_ids: set[str], edges: list[dict[str, Any]]
) -> set[str]:
    return {
        source
        for edge in edges
        if (source := str(edge.get("source") or ""))
        and str(edge.get("target") or "") in visible_ids
        and source not in visible_ids
    }


def _outgoing_neighbor_ids(
    visible_ids: set[str], edges: list[dict[str, Any]]
) -> set[str]:
    return {
        str(edge.get("target") or "")
        for edge in edges
        if str(edge.get("source") or "") in visible_ids
        and str(edge.get("target") or "")
        and str(edge.get("target") or "") not in visible_ids
    }


def _is_subprocess_node(
    focus_id: str | None, nodes_by_id: dict[str, dict[str, Any]]
) -> bool:
    if focus_id is None:
        return False
    node = nodes_by_id.get(focus_id)
    if node is None:
        return False
    kind = str(node.get("kind") or node.get("type") or "").strip().lower()
    return kind == "subprocess"


def _subprocess_parent(node: dict[str, Any]) -> str | None:
    value = node.get("subprocess_parent")
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_focus_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
