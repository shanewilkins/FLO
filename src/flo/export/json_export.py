"""JSON projection helpers for canonical FLO IR."""

from __future__ import annotations

import json
from typing import Any, Dict

from flo.compiler.ir.models import IR


def ir_to_schema_dict(ir: IR) -> Dict[str, Any]:
    """Project canonical IR into the JSON-schema contract shape."""
    process_id = ir.name or "generated"
    process: Dict[str, Any] = {"id": process_id, "name": process_id}
    if isinstance(ir.process_metadata, dict) and ir.process_metadata:
        process["metadata"] = ir.process_metadata

    nodes_out = [_node_to_schema(node) for node in ir.nodes]
    edges_out = _edges_to_schema(ir)

    return {
        "process": process,
        "nodes": nodes_out,
        "edges": edges_out,
    }


def _node_to_schema(node: Any) -> dict[str, Any]:
    node_entry: dict[str, Any] = {"id": node.id, "kind": node.type}
    attrs = node.attrs or {}
    if not isinstance(attrs, dict):
        return node_entry

    name = attrs.get("name")
    if name is not None:
        node_entry["name"] = name
    lane = attrs.get("lane")
    if lane is not None:
        node_entry["lane"] = lane
    note = attrs.get("note")
    if note is not None:
        node_entry["note"] = note
    inputs = attrs.get("inputs")
    if isinstance(inputs, list):
        node_entry["inputs"] = inputs
    outputs = attrs.get("outputs")
    if isinstance(outputs, list):
        node_entry["outputs"] = outputs
    metadata = attrs.get("metadata")
    if isinstance(metadata, dict):
        node_entry["metadata"] = metadata
    return node_entry


def _edges_to_schema(ir: IR) -> list[dict[str, Any]]:
    if ir.edges:
        return [_edge_to_schema(edge) for edge in ir.edges]
    return _legacy_edges_from_node_attrs(ir)


def _edge_to_schema(edge: Any) -> dict[str, Any]:
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
    return edge_entry


def _legacy_edges_from_node_attrs(ir: IR) -> list[dict[str, Any]]:
    edges_out: list[dict[str, Any]] = []
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
    return edges_out


def ir_to_schema_json(ir: IR, *, indent: int | None = 2) -> str:
    """Serialize in-memory IR as schema-shaped JSON export text."""
    payload = ir_to_schema_dict(ir)
    if indent is None or int(indent) <= 0:
        return json.dumps(payload, separators=(",", ":"))
    return json.dumps(payload, indent=int(indent))
