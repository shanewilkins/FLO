"""Schema-shaped projection helpers for canonical FLO IR.

These helpers define how canonical IR is projected into the JSON-schema
contract shape. The projection is neutral to validation and export so neither
layer needs to own the transformation.
"""

from __future__ import annotations

from typing import Any, TypeAlias, cast

from .models import IR, Edge, Node
from flo.schema.render_metadata import (
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)

JsonValue: TypeAlias = Any
JsonObject: TypeAlias = dict[str, JsonValue]
JsonArray: TypeAlias = list[JsonObject]


def ir_to_schema_dict(ir: IR) -> JsonObject:
    """Project canonical IR into the JSON-schema contract shape."""
    process_metadata = (
        ir.process_metadata if isinstance(ir.process_metadata, dict) else {}
    )
    process_id = _resolve_process_field(
        process_metadata, PROCESS_METADATA_PROCESS_ID_KEY, fallback=ir.name
    )
    process_name = _resolve_process_field(
        process_metadata, PROCESS_METADATA_PROCESS_NAME_KEY, fallback=ir.name
    )

    process: JsonObject = {"id": process_id, "name": process_name}
    if process_metadata:
        process["metadata"] = process_metadata

    nodes_out = [_node_to_schema(node) for node in ir.nodes]
    edges_out = _edges_to_schema(ir)

    return {
        "process": process,
        "nodes": nodes_out,
        "edges": edges_out,
    }


def _resolve_process_field(
    process_metadata: JsonObject, metadata_key: str, *, fallback: str | None
) -> str:
    value = process_metadata.get(metadata_key)
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(fallback, str) and fallback.strip():
        return fallback
    return "generated"


def _node_to_schema(node: Node) -> JsonObject:
    node_entry: JsonObject = {"id": node.id, "kind": node.type}
    attrs = _normalize_json_object(node.attrs)

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
    *, source: JsonObject, target: JsonObject, keys: tuple[str, ...]
) -> None:
    for key in keys:
        value = source.get(key)
        if value is not None:
            target[key] = value


def _copy_optional_lists(
    *, source: JsonObject, target: JsonObject, keys: tuple[str, ...]
) -> None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list):
            target[key] = value


def _edges_to_schema(ir: IR) -> JsonArray:
    if ir.edges:
        return [_edge_to_schema(edge) for edge in ir.edges]
    return _legacy_edges_from_node_attrs(ir)


def _edge_to_schema(edge: Edge) -> JsonObject:
    edge_entry: JsonObject = {
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


def _legacy_edges_from_node_attrs(ir: IR) -> JsonArray:
    edges_out: JsonArray = []
    edge_idx = 0
    for node in ir.nodes:
        attrs = _normalize_json_object(node.attrs)
        targets_value = attrs.get("edges")
        if not isinstance(targets_value, list):
            continue
        targets = cast(list[Any], targets_value)
        for target in targets:
            edges_out.append(
                {"id": f"e_{edge_idx}", "source": node.id, "target": str(target)}
            )
            edge_idx += 1
    return edges_out


def _normalize_json_object(value: object) -> JsonObject:
    if isinstance(value, dict):
        return cast(JsonObject, value)
    return {}
