"""Deterministic port assignment for the layout core.

Phase 4 keeps routing intentionally boring: each node gets one ingress side and
one egress side based on orientation, with ordered slots on those sides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import PlacementPlan

PortRole = Literal["in", "out"]
PortSide = Literal["n", "e", "s", "w"]


@dataclass(frozen=True)
class PortSpec:
    """Resolved port location for one edge endpoint on a node."""

    node_id: str
    side: PortSide
    slot_index: int
    role: PortRole


def build_port_assignments(
    *,
    placement: PlacementPlan,
    edges: list[tuple[str, str]],
) -> tuple[dict[tuple[str, str], PortSpec], dict[tuple[str, str], PortSpec]]:
    """Return deterministic source/target port specs for each logical edge."""
    source_side = _egress_side(placement.orientation)
    target_side = _ingress_side(placement.orientation)
    node_order = _node_order_index(placement)

    outgoing = _group_outgoing_edges(edges=edges, node_line_index=placement.node_line_index)
    incoming = _group_incoming_edges(edges=edges, node_line_index=placement.node_line_index)

    source_ports = _assign_ports(
        grouped_edges=outgoing,
        side=source_side,
        role="out",
        order_index=node_order,
    )
    target_ports = _assign_ports(
        grouped_edges=incoming,
        side=target_side,
        role="in",
        order_index=node_order,
    )
    return source_ports, target_ports


def _egress_side(orientation: str) -> PortSide:
    return "s" if orientation == "tb" else "e"


def _ingress_side(orientation: str) -> PortSide:
    return "n" if orientation == "tb" else "w"


def _node_order_index(placement: PlacementPlan) -> dict[str, tuple[int, int]]:
    index: dict[str, tuple[int, int]] = {}
    for line in placement.lines:
        for node_pos, node_id in enumerate(line.node_ids):
            index[node_id] = (line.line_index, node_pos)
    return index


def _group_outgoing_edges(
    *,
    edges: list[tuple[str, str]],
    node_line_index: dict[str, int],
) -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        source, target = edge
        if source not in node_line_index or target not in node_line_index:
            continue
        grouped.setdefault(source, []).append(edge)
    return grouped


def _group_incoming_edges(
    *,
    edges: list[tuple[str, str]],
    node_line_index: dict[str, int],
) -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        source, target = edge
        if source not in node_line_index or target not in node_line_index:
            continue
        grouped.setdefault(target, []).append(edge)
    return grouped


def _assign_ports(
    *,
    grouped_edges: dict[str, list[tuple[str, str]]],
    side: PortSide,
    role: PortRole,
    order_index: dict[str, tuple[int, int]],
) -> dict[tuple[str, str], PortSpec]:
    assignments: dict[tuple[str, str], PortSpec] = {}
    for node_id, node_edges in grouped_edges.items():
        sorted_edges = sorted(node_edges, key=lambda edge: _edge_sort_key(edge=edge, role=role, order_index=order_index))
        for slot_index, edge in enumerate(sorted_edges):
            assignments[edge] = PortSpec(node_id=node_id, side=side, slot_index=slot_index, role=role)
    return assignments


def _edge_sort_key(
    *,
    edge: tuple[str, str],
    role: PortRole,
    order_index: dict[str, tuple[int, int]],
) -> tuple[int, int, str]:
    source, target = edge
    remote_node = source if role == "in" else target
    line_index, node_pos = order_index.get(remote_node, (10**9, 10**9))
    return (line_index, node_pos, remote_node)