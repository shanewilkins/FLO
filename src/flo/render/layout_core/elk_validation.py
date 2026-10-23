"""Validation helpers for FLO-owned ELK requests and responses."""

from __future__ import annotations

from flo.errors import RenderError

from .elk_contracts import ElkLayoutRequest


def validate_elk_request_namespaces(
    request: ElkLayoutRequest,
    *,
    reserved_ids: frozenset[str] = frozenset(),
    reserved_prefixes: tuple[str, ...] = (),
    synthetic_lane_ids: set[str] | None = None,
) -> None:
    """Raise when a render-visible ELK namespace is ambiguous."""
    node_ids = [node.id for node in request.nodes]
    lane_ids = [lane.id for lane in request.lanes]
    helper_node_ids = [
        str(node["id"]) for node in request.serialization.auxiliary_nodes
    ]

    _raise_on_duplicates(kind="node", ids=node_ids)
    _raise_on_duplicates(kind="lane", ids=lane_ids)
    _raise_on_cross_namespace_collisions(
        left_kind="node",
        left_ids=node_ids,
        right_kind="lane",
        right_ids=lane_ids,
    )
    _raise_on_cross_namespace_collisions(
        left_kind="node",
        left_ids=node_ids,
        right_kind="helper node",
        right_ids=helper_node_ids,
    )
    _raise_on_cross_namespace_collisions(
        left_kind="lane",
        left_ids=lane_ids,
        right_kind="helper node",
        right_ids=helper_node_ids,
    )
    _raise_on_reserved_ids(
        kind="node",
        ids=node_ids,
        reserved_ids=reserved_ids,
        reserved_prefixes=reserved_prefixes,
    )
    _raise_on_reserved_ids(
        kind="lane",
        ids=lane_ids,
        ignore_ids=synthetic_lane_ids,
        reserved_ids=reserved_ids,
        reserved_prefixes=reserved_prefixes,
    )


def _raise_on_duplicates(*, kind: str, ids: list[str]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for current_id in ids:
        if current_id in seen and current_id not in duplicates:
            duplicates.append(current_id)
        seen.add(current_id)
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise RenderError(
            f"Duplicate {kind} ids are not allowed in ELK render request: {duplicate_text}"
        )


def _raise_on_cross_namespace_collisions(
    *,
    left_kind: str,
    left_ids: list[str],
    right_kind: str,
    right_ids: list[str],
) -> None:
    collisions = sorted(set(left_ids).intersection(right_ids))
    if collisions:
        collision_text = ", ".join(collisions)
        raise RenderError(
            f"ELK render namespace collision between {left_kind} ids and {right_kind} ids: {collision_text}"
        )


def _raise_on_reserved_ids(
    *,
    kind: str,
    ids: list[str],
    ignore_ids: set[str] | None = None,
    reserved_ids: frozenset[str],
    reserved_prefixes: tuple[str, ...],
) -> None:
    ignored = ignore_ids or set()
    reserved = sorted(
        current_id
        for current_id in set(ids)
        if current_id not in ignored
        and (current_id in reserved_ids or current_id.startswith(reserved_prefixes))
    )
    if reserved:
        reserved_text = ", ".join(reserved)
        raise RenderError(
            f"Renderer-reserved {kind} ids are not allowed in ELK render request: {reserved_text}"
        )
