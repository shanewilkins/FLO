"""SPPM-owned ELK serialization choices and namespace policy."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..layout_core.elk_contracts import ElkLayoutRequest, ElkSerialization
from .elk_helpers import (
    _root_layout_options,
    _sppm_branch_anchor_helpers,
    _sppm_port_id,
    _sppm_spacing_layout_options,
)
from .layout_spacing import transform_sppm_layout
from .strategy import should_emit_sppm_branch_anchors, sppm_port_constraints_value


def _sppm_cardinal_ports(node_id: str) -> list[dict[str, Any]]:
    sides = ("NORTH", "EAST", "SOUTH", "WEST")
    return [
        {
            "id": _sppm_port_id(node_id, side),
            "width": 0,
            "height": 0,
            "layoutOptions": {
                "elk.port.side": side,
                "elk.port.index": str(index),
            },
        }
        for index, side in enumerate(sides)
    ]


def prepare_sppm_request(request: ElkLayoutRequest) -> ElkLayoutRequest:
    """Attach SPPM serialization choices and the diagram-owned layout pass."""
    helpers, edges = ([], [])
    if should_emit_sppm_branch_anchors(has_lanes=bool(request.lanes)):
        helpers, edges = _sppm_branch_anchor_helpers(request=request)
    settings = ElkSerialization(
        root_options=_root_layout_options(request),
        lane_options={
            "elk.algorithm": "layered",
            "elk.direction": request.direction,
            "elk.edgeRouting": "ORTHOGONAL",
            **_sppm_spacing_layout_options(),
            "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
            "elk.layered.nodePlacement.bk.fixedAlignment": "TOP",
        },
        node_overrides={
            node.id: {
                "layoutOptions": {"elk.portConstraints": sppm_port_constraints_value()},
                "ports": _sppm_cardinal_ports(node.id),
            }
            for node in request.nodes
        },
        edge_overrides={
            edge.id: {
                "sources": [
                    _sppm_port_id(edge.source_id, edge.source_port_side or "EAST")
                ],
                "targets": [
                    _sppm_port_id(edge.target_id, edge.target_port_side or "WEST")
                ],
            }
            for edge in request.edges
        },
        unlabeled_edge_ids=frozenset(
            edge.id
            for edge in request.edges
            if edge.rework_variant in {"branch", "return"}
        ),
        auxiliary_nodes=tuple(helpers),
        auxiliary_edges=tuple(edges),
        constrain_terminal_layers=_terminal_layer_constraints_are_safe(request),
    )
    return replace(
        request, serialization=settings, result_transform=transform_sppm_layout
    )


def _terminal_layer_constraints_are_safe(request: ElkLayoutRequest) -> bool:
    start_ids = [node.id for node in request.nodes if node.kind == "start"]
    end_ids = [node.id for node in request.nodes if node.kind == "end"]
    if len(start_ids) != 1 or len(end_ids) != 1:
        return False
    incoming_ids = {edge.target_id for edge in request.edges}
    outgoing_ids = {edge.source_id for edge in request.edges}
    return start_ids[0] not in incoming_ids and end_ids[0] not in outgoing_ids
