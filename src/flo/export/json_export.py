"""JSON projection helpers for canonical FLO IR."""

from __future__ import annotations

import json
from typing import Any, Dict

from flo.compiler.ir.models import IR


def ir_to_schema_dict(ir: IR) -> Dict[str, Any]:
    """Project canonical IR into the JSON-schema contract shape."""
    process_id = ir.name or "generated"
    process = {"id": process_id, "name": process_id}

    nodes_out: list[dict[str, Any]] = []
    edges_out: list[dict[str, Any]] = []

    for node in ir.nodes:
        node_entry: dict[str, Any] = {"id": node.id, "kind": node.type}
        attrs = node.attrs or {}
        if isinstance(attrs, dict):
            name = attrs.get("name")
            if name is not None:
                node_entry["name"] = name
            lane = attrs.get("lane")
            if lane is not None:
                node_entry["lane"] = lane
            metadata = attrs.get("metadata")
            if isinstance(metadata, dict):
                node_entry["metadata"] = metadata
        nodes_out.append(node_entry)

    if ir.edges:
        for edge in ir.edges:
            edge_entry: dict[str, Any] = {
                "source": edge.source,
                "target": edge.target,
            }
            if edge.id is not None:
                edge_entry["id"] = edge.id
            if edge.outcome is not None:
                edge_entry["outcome"] = edge.outcome
            if edge.label is not None:
                edge_entry["label"] = edge.label
            if isinstance(edge.metadata, dict):
                edge_entry["metadata"] = edge.metadata
            edges_out.append(edge_entry)
    else:
        # Back-compat projection for legacy node attrs edge lists.
        edge_idx = 0
        for node in ir.nodes:
            attrs = node.attrs or {}
            if not isinstance(attrs, dict):
                continue
            targets = attrs.get("edges") or []
            if not isinstance(targets, list):
                continue
            for target in targets:
                edges_out.append({"id": f"e_{edge_idx}", "source": node.id, "target": str(target)})
                edge_idx += 1

    return {
        "process": process,
        "nodes": nodes_out,
        "edges": edges_out,
    }


def ir_to_schema_json(ir: IR, *, indent: int = 2) -> str:
    """Serialize an IR instance as schema-shaped JSON text."""
    return json.dumps(ir_to_schema_dict(ir), indent=indent)
