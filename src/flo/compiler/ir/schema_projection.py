"""Schema-shaped projection helpers for canonical FLO IR.

These helpers define how canonical IR is projected into the JSON-schema
contract shape. The projection is neutral to validation and export so neither
layer needs to own the transformation.
"""

from __future__ import annotations

from typing import Any

from .models import IR


def ir_to_schema_dict(ir: IR) -> dict[str, Any]:
    """Project canonical IR into the JSON-schema contract shape."""
    process_id = ir.name or "generated"
    process: dict[str, Any] = {"id": process_id, "name": process_id}
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

    _copy_optional_scalars(
        source=attrs,
        target=node_entry,
        keys=("name", "lane", "note", "location"),
    )
    _copy_optional_lists(
        source=attrs,
        target=node_entry,
        keys=(
            "workers",
            "equipment",
            "inputs",
            "outputs",
            "consumes",
            "produces",
            "performed_by",
            "uses",
        ),
    )
    metadata = attrs.get("metadata")
    if isinstance(metadata, dict):
        node_entry["metadata"] = metadata
    return node_entry


def _copy_optional_scalars(
    *, source: dict[str, Any], target: dict[str, Any], keys: tuple[str, ...]
) -> None:
    for key in keys:
        value = source.get(key)
        if value is not None:
            target[key] = value


def _copy_optional_lists(
    *, source: dict[str, Any], target: dict[str, Any], keys: tuple[str, ...]
) -> None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list):
            target[key] = value


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
    if edge.edge_type is not None:
        edge_entry["edge_type"] = edge.edge_type
    if edge.handoff is not None:
        edge_entry["handoff"] = edge.handoff
    if edge.rework is not None:
        edge_entry["rework"] = edge.rework
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
            edges_out.append(
                {"id": f"e_{edge_idx}", "source": node.id, "target": str(target)}
            )
            edge_idx += 1
    return edges_out
