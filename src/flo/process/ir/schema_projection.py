"""Schema-shaped projection helpers for canonical FLO IR.

These helpers define how canonical IR is projected into the JSON-schema
contract shape. The projection is neutral to validation and export so neither
layer needs to own the transformation.
"""

from __future__ import annotations

from typing import Any

from flo.process.schema.render_metadata import (
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)

from ._internal_shape import _edge_to_dict, _node_to_dict
from .models import IR, Edge, Node

type JsonValue = Any
type JsonObject = dict[str, JsonValue]
type JsonArray = list[JsonObject]


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
    if ir.process_version is not None:
        process["version"] = ir.process_version
    if ir.process_owner is not None:
        process["owner"] = ir.process_owner
    if ir.business_units != []:
        process["business_units"] = ir.business_units
    if ir.lead_time is not None:
        process["lead_time"] = ir.lead_time
    if ir.extensions is not None:
        process["extensions"] = ir.extensions
    _copy_explicit_metadata_field(process, "render", ir.render_intent)
    _copy_explicit_metadata_field(process, "items", ir.items)
    _copy_explicit_metadata_field(process, "resources", ir.resources)
    _copy_explicit_metadata_field(process, "locations", ir.locations)

    nodes_out = [_node_to_schema(node) for node in ir.nodes]
    edges_out = [_edge_to_schema(edge) for edge in ir.edges]

    projected: JsonObject = {
        "process": process,
        "nodes": nodes_out,
        "edges": edges_out,
    }
    if ir.lanes is not None:
        projected["lanes"] = ir.lanes
    return projected


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
    output = _node_to_dict(node)
    output["kind"] = output.pop("type")
    for key in ("consumes", "produces", "performed_by", "uses"):
        if output[key] == []:
            del output[key]
    return output


def _edge_to_schema(edge: Edge) -> JsonObject:
    return _edge_to_dict(edge)


def _copy_explicit_metadata_field(
    metadata: JsonObject, key: str, value: object
) -> None:
    if value is not None:
        metadata[key] = value
