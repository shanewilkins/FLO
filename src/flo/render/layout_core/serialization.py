"""Serialize explicit diagram-supplied ELK settings without diagram policy."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .elk_contracts import ElkLayoutNode, ElkLayoutRequest
from .elk_support import serialize_edge, serialize_node


def serialize_elk_layout_request(request: ElkLayoutRequest) -> dict[str, Any]:
    """Lower a FLO-owned ELK request into an ELK-shaped payload."""
    node_by_id = {node.id: node for node in request.nodes}
    helper_nodes = request.serialization.auxiliary_nodes
    helper_edges = request.serialization.auxiliary_edges
    constrain_terminal_layers = request.serialization.constrain_terminal_layers

    children = _serialize_lane_children(
        request=request,
        node_by_id=node_by_id,
        constrain_terminal_layers=constrain_terminal_layers,
    )

    assigned_node_ids = {
        node_id
        for lane in request.lanes
        for node_id in lane.node_ids
        if node_id in node_by_id
    }
    children.extend(
        _serialize_unassigned_nodes(
            request=request,
            assigned_node_ids=assigned_node_ids,
            constrain_terminal_layers=constrain_terminal_layers,
        )
    )

    if helper_nodes:
        children.extend(helper_nodes)

    serialized_edges = _serialize_request_edges(
        request=request, helper_edges=helper_edges
    )

    return deepcopy(
        {
            "id": f"flo:{request.diagram}",
            "layoutOptions": request.serialization.root_options
            or {"elk.algorithm": "layered", "elk.direction": request.direction},
            "children": children,
            "edges": serialized_edges,
        }
    )


def _serialize_lane_children(
    *,
    request: ElkLayoutRequest,
    node_by_id: dict[str, ElkLayoutNode],
    constrain_terminal_layers: bool,
) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for lane_index, lane in enumerate(request.lanes):
        lane_layout_options: dict[str, str] = {
            "elk.partitioning.partition": str(lane_index)
        }
        lane_layout_options.update(request.serialization.lane_options)
        children.append(
            {
                "id": lane.id,
                "labels": [{"text": lane.label}],
                "layoutOptions": lane_layout_options,
                "children": [
                    serialize_node(
                        node_by_id[node_id],
                        settings=request.serialization,
                        constrain_terminal_layers=constrain_terminal_layers,
                    )
                    for node_id in lane.node_ids
                    if node_id in node_by_id
                ],
            }
        )
    return children


def _serialize_unassigned_nodes(
    *,
    request: ElkLayoutRequest,
    assigned_node_ids: set[str],
    constrain_terminal_layers: bool,
) -> list[dict[str, Any]]:
    return [
        serialize_node(
            node,
            settings=request.serialization,
            constrain_terminal_layers=constrain_terminal_layers,
        )
        for node in request.nodes
        if node.id not in assigned_node_ids
    ]


def _serialize_request_edges(
    *,
    request: ElkLayoutRequest,
    helper_edges: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    serialized_edges = [
        serialize_edge(edge, settings=request.serialization) for edge in request.edges
    ]
    if helper_edges:
        serialized_edges.extend(helper_edges)
    return serialized_edges
