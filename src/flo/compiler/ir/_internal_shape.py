"""Private helpers for IR internal-shape serialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import IR, Edge, Node


def ir_to_internal_dict(ir: IR) -> dict[str, Any]:
    """Return internal-shape dict for in-memory canonical IR."""
    return {
        "name": ir.name,
        "nodes": [_node_to_dict(node) for node in ir.nodes],
        "edges": [_edge_to_dict(edge) for edge in ir.edges],
        "process_metadata": ir.process_metadata or {},
    }


def ir_from_internal_dict(data: dict[str, Any]) -> IR:
    """Build canonical IR from internal-shape dictionary payload."""
    nodes: list[Node] = []
    for node_data in data.get("nodes", []):
        if not isinstance(node_data, dict):
            continue
        nodes.append(
            Node(
                id=node_data.get("id", ""),
                type=node_data.get("type", ""),
                attrs=node_data.get("attrs", {}),
            )
        )

    edges: list[Edge] = []
    for edge_data in data.get("edges", []):
        if not isinstance(edge_data, dict):
            continue
        edges.append(
            Edge(
                source=edge_data.get("source", ""),
                target=edge_data.get("target", ""),
                id=edge_data.get("id"),
                outcome=edge_data.get("outcome"),
                label=edge_data.get("label"),
                edge_type=edge_data.get("edge_type"),
                handoff=edge_data.get("handoff"),
                rework=edge_data.get("rework"),
                metadata=edge_data.get("metadata"),
            )
        )

    process_metadata = data.get("process_metadata")
    if not isinstance(process_metadata, dict):
        process_metadata = None

    return IR(
        name=data.get("name", ""),
        nodes=nodes,
        edges=edges,
        process_metadata=process_metadata,
    )


def ir_to_internal_json(ir: IR, path: Path | str | None = None) -> str:
    """Serialize internal IR shape to JSON and optionally write to path."""
    payload = ir_to_internal_dict(ir)
    output = json.dumps(payload, indent=2)
    if path:
        Path(path).write_text(output, encoding="utf-8")
    return output


def _node_to_dict(node: Node) -> dict[str, Any]:
    return {"id": node.id, "type": node.type, "attrs": node.attrs or {}}


def _edge_to_dict(edge: Edge) -> dict[str, Any]:
    output: dict[str, Any] = {"source": edge.source, "target": edge.target}
    if edge.id is not None:
        output["id"] = edge.id
    if edge.outcome is not None:
        output["outcome"] = edge.outcome
    if edge.label is not None:
        output["label"] = edge.label
    if edge.edge_type is not None:
        output["edge_type"] = edge.edge_type
    if edge.handoff is not None:
        output["handoff"] = edge.handoff
    if edge.rework is not None:
        output["rework"] = edge.rework
    if edge.metadata is not None:
        output["metadata"] = edge.metadata
    return output
