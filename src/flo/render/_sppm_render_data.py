"""Normalized render-data helpers for SPPM DOT rendering.

This module isolates the shape adaptation between canonical IR or dict-like
process inputs and the renderer's internal node/edge dictionaries. It exists so
graph assembly and node rendering do not each need to understand both input
surfaces.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from flo.compiler.ir.models import IR

SppmRenderNode: TypeAlias = dict[str, Any]
SppmRenderEdge: TypeAlias = dict[str, Any]

__all__ = [
    "SppmRenderEdge",
    "SppmRenderNode",
    "build_step_numbering",
    "extract_sppm_nodes_edges",
    "port_counts_by_node",
]


def extract_sppm_nodes_edges(
    process: IR | dict[str, Any] | None,
) -> tuple[list[SppmRenderNode], list[SppmRenderEdge]]:
    """Return normalized renderer dictionaries for SPPM nodes and edges."""
    if process is None:
        return [], []
    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_sppm_from_ir(process)
    if isinstance(process, dict):
        return _extract_sppm_from_dict(process)
    return [], []


def build_step_numbering(nodes: list[SppmRenderNode]) -> dict[str, int]:
    """Return stable sequential step numbers for non-start/end nodes."""
    numbering: dict[str, int] = {}
    sequence = 1
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "task").lower()
        if kind in {"start", "end"}:
            continue
        numbering[node_id] = sequence
        sequence += 1
    return numbering


def port_counts_by_node(routing_plan: Any) -> dict[str, dict[str, int]]:
    """Return max in/out port counts for each routed node."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0})
    for route in routing_plan.route_plan.routes.values():
        counts[route.source_port.node_id]["out"] = max(
            counts[route.source_port.node_id]["out"], route.source_port.slot_index + 1
        )
        counts[route.target_port.node_id]["in"] = max(
            counts[route.target_port.node_id]["in"], route.target_port.slot_index + 1
        )
    return dict(counts)


def _extract_sppm_from_ir(process: Any) -> tuple[list[SppmRenderNode], list[SppmRenderEdge]]:
    nodes: list[SppmRenderNode] = []
    for node in getattr(process, "nodes", []) or []:
        attrs: dict[str, Any] = (getattr(node, "attrs", None) or {}) if hasattr(node, "attrs") else {}
        raw_metadata = attrs.get("metadata") if isinstance(attrs, dict) else None
        raw_workers = attrs.get("workers") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": attrs.get("name") if isinstance(attrs, dict) else None,
                "note": attrs.get("note") if isinstance(attrs, dict) else None,
                "metadata": raw_metadata if isinstance(raw_metadata, dict) else {},
                "workers": raw_workers if isinstance(raw_workers, list) else [],
                "subprocess_parent": attrs.get("subprocess_parent") if isinstance(attrs, dict) else None,
            }
        )

    edges: list[SppmRenderEdge] = []
    for edge in getattr(process, "edges", []) or []:
        edges.append(
            {
                "source": getattr(edge, "source", None),
                "target": getattr(edge, "target", None),
                "outcome": getattr(edge, "outcome", None),
                "label": getattr(edge, "label", None),
                "edge_type": getattr(edge, "edge_type", None),
                "rework": getattr(edge, "rework", None),
                "metadata": getattr(edge, "metadata", None),
            }
        )
    return nodes, edges


def _get_node_attr(node: SppmRenderNode, field: str, *, expected_type: type) -> Any:
    value = node.get(field)
    if isinstance(value, expected_type):
        return value
    attrs = node.get("attrs")
    if isinstance(attrs, dict):
        fallback = attrs.get(field)
        if isinstance(fallback, expected_type):
            return fallback
    return None


def _extract_sppm_from_dict(
    process: dict[str, Any],
) -> tuple[list[SppmRenderNode], list[SppmRenderEdge]]:
    nodes_raw = process.get("nodes") or []
    edges_raw = process.get("edges") or []

    nodes: list[SppmRenderNode] = []
    for node in nodes_raw:
        if not isinstance(node, dict):
            continue
        metadata = _get_node_attr(node, "metadata", expected_type=dict) or {}
        nodes.append(
            {
                "id": node.get("id"),
                "kind": node.get("kind") or node.get("type") or "task",
                "name": node.get("name"),
                "note": node.get("note"),
                "metadata": metadata,
                "workers": _get_node_attr(node, "workers", expected_type=list) or [],
                "subprocess_parent": _get_node_attr(node, "subprocess_parent", expected_type=str),
            }
        )

    edges = [edge for edge in edges_raw if isinstance(edge, dict)]
    return nodes, edges