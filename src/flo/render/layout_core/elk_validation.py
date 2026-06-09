"""Validation helpers for FLO-owned ELK requests and responses."""

from __future__ import annotations

from flo.services.errors import RenderError

from .elk_contracts import ElkLayoutRequest
from .elk_sppm_helpers import _sppm_branch_anchor_helpers
from .sppm_strategy import should_emit_sppm_branch_anchors

_RESERVED_RENDER_IDS = {
    "unassigned",
    "__sppm_row_mainline",
    "__sppm_row_rework",
}


def validate_elk_request_namespaces(request: ElkLayoutRequest) -> None:
    """Raise when a render-visible ELK namespace is ambiguous."""
    node_ids = [node.id for node in request.nodes]
    lane_ids = [lane.id for lane in request.lanes]
    helper_node_ids = _helper_node_ids(request)

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
    _raise_on_reserved_ids(kind="node", ids=node_ids)
    _raise_on_reserved_ids(
        kind="lane",
        ids=lane_ids,
        ignore_ids=_synthetic_lane_ids(request),
    )


def _synthetic_lane_ids(request: ElkLayoutRequest) -> set[str]:
    node_lane_by_id = {node.id: node.lane_id for node in request.nodes}
    synthetic: set[str] = set()
    for lane in request.lanes:
        if lane.id != "unassigned":
            continue
        if lane.node_ids and all(
            node_lane_by_id.get(node_id) is None for node_id in lane.node_ids
        ):
            synthetic.add(lane.id)
    return synthetic


def _helper_node_ids(request: ElkLayoutRequest) -> list[str]:
    if request.diagram != "sppm":
        return []
    if not should_emit_sppm_branch_anchors(has_lanes=bool(request.lanes)):
        return []
    helper_nodes, _helper_edges = _sppm_branch_anchor_helpers(request=request)
    return [
        str(node.get("id") or "") for node in helper_nodes if str(node.get("id") or "")
    ]


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
) -> None:
    ignored = ignore_ids or set()
    reserved = sorted(
        current_id
        for current_id in set(ids)
        if current_id not in ignored
        and (current_id in _RESERVED_RENDER_IDS or current_id.startswith("__sppm_"))
    )
    if reserved:
        reserved_text = ", ".join(reserved)
        raise RenderError(
            f"Renderer-reserved {kind} ids are not allowed in ELK render request: {reserved_text}"
        )
