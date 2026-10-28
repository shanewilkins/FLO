"""Schema-shaped projection helpers for canonical FLO IR.

These helpers define how canonical IR is projected into the JSON-schema
contract shape. The projection is neutral to validation and export so neither
layer needs to own the transformation.
"""

from __future__ import annotations

from typing import Any, cast

from flo.process.schema.render_metadata import (
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)

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
    if isinstance(ir.process_owner, dict):
        process["owner"] = ir.process_owner
    if ir.business_units:
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
    edges_out = _edges_to_schema(ir)

    projected: JsonObject = {
        "process": process,
        "nodes": nodes_out,
        "edges": edges_out,
    }
    if ir.lanes:
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
    node_entry: JsonObject = {"id": node.id, "kind": node.type}
    attrs = _normalize_json_object(node.attrs)

    for key in ("name", "description", "lane", "location", "value_class"):
        value = getattr(node, key)
        if value is not None:
            node_entry[key] = value
    branch = attrs.get("branch")
    if isinstance(branch, dict):
        node_entry["branch"] = branch
    if node.subprocess_parent is not None:
        node_entry["subprocess_parent"] = node.subprocess_parent
    for key in ("consumes", "produces", "performed_by", "uses"):
        value = getattr(node, key)
        if value or not isinstance(value, list):
            node_entry[key] = value
    for key in ("cycle_time", "wait_time", "changeover_time", "extensions"):
        value = getattr(node, key)
        if value is not None:
            node_entry[key] = value
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
    if edge.route is not None:
        edge_entry["route"] = edge.route
    if edge.label is not None:
        edge_entry["label"] = edge.label
    if edge.handoff is not None:
        edge_entry["handoff"] = edge.handoff
    if edge.rework is not None:
        edge_entry["rework"] = edge.rework
    if edge.extensions is not None:
        edge_entry["extensions"] = edge.extensions
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


def _copy_explicit_metadata_field(
    metadata: JsonObject, key: str, value: object
) -> None:
    if value is not None:
        metadata[key] = value
