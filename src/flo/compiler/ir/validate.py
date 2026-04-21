"""Validation helpers for the FLO IR types (now under compiler.ir)."""
from __future__ import annotations

from typing import Any

from .models import IR
from .enums import ProcessValueClass
from flo.services.errors import ValidationError
from flo.export import ir_to_schema_dict
from pathlib import Path
import json

_MEASURE_UNITS = {"mg", "g", "kg", "ml", "l", "mm", "cm", "m"}
_TIME_UNITS = {"s", "m", "min", "hr", "d"}
_SPATIAL_UNITS = {"mm", "cm", "m", "in", "ft"}

try:
    import jsonschema  # type: ignore
    _JSONSCHEMA_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    jsonschema = None  # type: ignore
    _JSONSCHEMA_AVAILABLE = False


def validate_ir(obj: Any) -> None:
    """Validate a basic IR instance for structural correctness.

    Raises `ValidationError` on failure.
    """
    if not isinstance(obj, IR):
        raise ValidationError("E1000: object is not an IR instance")

    if not obj.nodes:
        raise ValidationError("E1001: IR must contain at least one node")

    ids = [n.id for n in obj.nodes]
    if len(ids) != len(set(ids)):
        raise ValidationError("E1002: node ids must be unique")

    _validate_start_nodes(obj)
    _validate_edge_resolution(obj, ids)
    incoming_counts, outgoing_counts = _build_edge_degree_maps(obj, ids)
    _validate_decision_nodes(obj, outgoing_counts)
    _validate_queue_nodes(obj, incoming_counts, outgoing_counts)
    _validate_node_io_lists(obj)
    _validate_node_time_metadata(obj)
    _validate_node_value_class(obj)
    _validate_process_resources(obj)
    _validate_node_connectivity(obj, incoming_counts, outgoing_counts)
    _validate_global_reachability(obj)


def _validate_start_nodes(obj: IR) -> None:
    start_nodes = [n for n in obj.nodes if (n.type or "").lower() == "start"]
    if len(start_nodes) != 1:
        raise ValidationError("E1003: IR must contain exactly one start node")


def _validate_edge_resolution(obj: IR, ids: list[str]) -> None:
    known_ids = set(ids)
    for edge in obj.edges:
        if edge.source not in known_ids or edge.target not in known_ids:
            raise ValidationError(f"E1004: edge endpoint unresolved: {edge.source} -> {edge.target}")


def _build_edge_degree_maps(obj: IR, ids: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    known_ids = set(ids)
    incoming_counts: dict[str, int] = {node_id: 0 for node_id in known_ids}
    outgoing_counts: dict[str, int] = {node_id: 0 for node_id in known_ids}
    for edge in obj.edges:
        if edge.target in incoming_counts:
            incoming_counts[edge.target] += 1
        if edge.source in outgoing_counts:
            outgoing_counts[edge.source] += 1
    return incoming_counts, outgoing_counts


def _validate_decision_nodes(obj: IR, outgoing_counts: dict[str, int]) -> None:
    for node in obj.nodes:
        if (node.type or "").lower() != "decision":
            continue
        if outgoing_counts.get(node.id, 0) < 2:
            raise ValidationError(
                f"E1005: decision node '{node.id}' must have at least two outgoing edges"
            )


def _validate_queue_nodes(obj: IR, incoming_counts: dict[str, int], outgoing_counts: dict[str, int]) -> None:
    for node in obj.nodes:
        if (node.type or "").lower() != "queue":
            continue

        metadata = _extract_node_metadata(node)
        _validate_queue_metadata(node_id=node.id, metadata=metadata)

        if incoming_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1103: queue node '{node.id}' must have at least one incoming edge"
            )
        if outgoing_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1104: queue node '{node.id}' must have at least one outgoing edge"
            )


def _validate_node_connectivity(
    obj: IR,
    incoming_counts: dict[str, int],
    outgoing_counts: dict[str, int],
) -> None:
    for node in obj.nodes:
        node_type = (node.type or "").lower()

        if node_type != "start" and incoming_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1006: node '{node.id}' must have at least one predecessor"
            )

        if node_type != "end" and outgoing_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1007: node '{node.id}' must have at least one successor"
            )


def _validate_global_reachability(obj: IR) -> None:
    node_ids = [node.id for node in obj.nodes]
    adjacency, reverse_adjacency = _build_adjacency_maps(node_ids=node_ids, edges=obj.edges)
    start_nodes = _collect_node_ids_by_type(obj=obj, node_type="start")
    end_nodes = _collect_node_ids_by_type(obj=obj, node_type="end")

    _ensure_end_nodes_present(end_nodes=end_nodes)
    _ensure_all_nodes_reachable_from_start(obj=obj, start_nodes=start_nodes, adjacency=adjacency)
    _ensure_all_nodes_can_reach_end(obj=obj, end_nodes=end_nodes, reverse_adjacency=reverse_adjacency)


def _build_adjacency_maps(
    node_ids: list[str],
    edges: list[Any],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    id_set = set(node_ids)
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}
    reverse_adjacency: dict[str, set[str]] = {node_id: set() for node_id in id_set}

    for edge in edges:
        if edge.source in adjacency and edge.target in adjacency:
            adjacency[edge.source].add(edge.target)
            reverse_adjacency[edge.target].add(edge.source)

    return adjacency, reverse_adjacency


def _collect_node_ids_by_type(obj: IR, node_type: str) -> list[str]:
    return [node.id for node in obj.nodes if (node.type or "").lower() == node_type]


def _ensure_end_nodes_present(end_nodes: list[str]) -> None:
    if not end_nodes:
        raise ValidationError("E1010: IR must contain at least one end node")


def _ensure_all_nodes_reachable_from_start(
    obj: IR,
    start_nodes: list[str],
    adjacency: dict[str, set[str]],
) -> None:
    reachable_from_start = _traverse(start_nodes, adjacency)
    for node in obj.nodes:
        if node.id not in reachable_from_start:
            raise ValidationError(f"E1008: node '{node.id}' is unreachable from start")


def _ensure_all_nodes_can_reach_end(
    obj: IR,
    end_nodes: list[str],
    reverse_adjacency: dict[str, set[str]],
) -> None:
    can_reach_end = _traverse(end_nodes, reverse_adjacency)
    for node in obj.nodes:
        if node.id not in can_reach_end:
            raise ValidationError(f"E1009: node '{node.id}' cannot reach any end node")


def _traverse(seed_ids: list[str], graph: dict[str, set[str]]) -> set[str]:
    visited: set[str] = set()
    stack: list[str] = list(seed_ids)
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for nxt in graph.get(current, set()):
            if nxt not in visited:
                stack.append(nxt)
    return visited


def _validate_queue_metadata(node_id: str, metadata: dict[str, Any]) -> None:
    if "queue_policy" not in metadata:
        raise ValidationError(
            f"E1101: queue node '{node_id}' missing required metadata.queue_policy"
        )

    capacity = metadata.get("buffer_capacity")
    if capacity is not None and (not isinstance(capacity, int) or capacity < 1):
        raise ValidationError(
            f"E1102: queue node '{node_id}' has invalid metadata.buffer_capacity; expected integer >= 1"
        )


def _validate_node_io_lists(obj: IR) -> None:
    for node in obj.nodes:
        attrs = getattr(node, "attrs", None)
        if not isinstance(attrs, dict):
            continue

        for field in ("inputs", "outputs"):
            value = attrs.get(field)
            if value is None:
                continue

            if not isinstance(value, list):
                raise ValidationError(
                    f"E1310: node '{node.id}' {field} must be a list"
                )

            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    raise ValidationError(
                        f"E1311: node '{node.id}' {field}[{index}] must be a non-empty string"
                    )


def _validate_node_time_metadata(obj: IR) -> None:
    for node in obj.nodes:
        metadata = _extract_node_metadata(node)
        for key, value in metadata.items():
            if not _is_node_time_metadata_key(key):
                continue
            _validate_node_time_metadata_value(node_id=node.id, key=key, value=value)


def _is_node_time_metadata_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False

    normalized = key.strip().lower()
    if normalized.endswith("_seconds"):
        # Existing second-based scalar keys remain supported.
        return False

    return normalized in {"time", "duration"} or normalized.endswith("_time") or normalized.endswith("_duration")


def _validate_node_time_metadata_value(node_id: str, key: str, value: Any) -> None:
    path = f"node '{node_id}' metadata.{key}"

    if not isinstance(value, dict):
        raise ValidationError(
            f"E1301: {path} must be an object with 'value' and 'unit'"
        )

    duration_value = value.get("value")
    if not isinstance(duration_value, (int, float)) or isinstance(duration_value, bool) or float(duration_value) < 0:
        raise ValidationError(
            f"E1302: {path}.value must be a number >= 0"
        )

    unit = value.get("unit")
    if not isinstance(unit, str) or unit.strip().lower() not in _TIME_UNITS:
        raise ValidationError(
            f"E1303: {path}.unit must be one of {sorted(_TIME_UNITS)}"
        )


def _validate_process_resources(obj: IR) -> None:
    process_metadata = getattr(obj, "process_metadata", None)
    if not isinstance(process_metadata, dict):
        return

    for resource_key in ("materials", "equipment", "locations", "workers"):
        resources = process_metadata.get(resource_key)
        if resources is None:
            continue
        _validate_resource_collection(resource_key=resource_key, collection=resources, path=resource_key)


def _validate_resource_collection(resource_key: str, collection: Any, path: str) -> None:
    if isinstance(collection, list):
        for index, resource in enumerate(collection):
            _validate_resource_item(resource_key=resource_key, path=f"{path}[{index}]", resource=resource)
        return

    if isinstance(collection, dict):
        group_label = collection.get("name")
        if "name" in collection and (not isinstance(group_label, str) or not group_label.strip()):
            raise ValidationError(
                f"E1201: process metadata '{path}.name' must be a non-empty string"
            )

        child_items = [(group_name, nested_collection) for group_name, nested_collection in collection.items() if group_name != "name"]
        if not child_items:
            raise ValidationError(
                f"E1201: process metadata '{path}' grouped objects must include at least one nested collection"
            )

        for group_name, nested_collection in child_items:
            if not isinstance(group_name, str) or not group_name.strip():
                raise ValidationError(
                    f"E1201: process metadata '{path}' group keys must be non-empty strings"
                )
            _validate_resource_collection(
                resource_key=resource_key,
                collection=nested_collection,
                path=f"{path}.{group_name}",
            )
        return

    raise ValidationError(
        f"E1201: process metadata '{path}' must be a list or grouped object"
    )


def _validate_resource_item(resource_key: str, path: str, resource: Any) -> None:
    if not isinstance(resource, dict):
        raise ValidationError(
            f"E1202: {path} must be an object"
        )

    resource_id = resource.get("id")
    if resource_id is not None and not isinstance(resource_id, str):
        raise ValidationError(
            f"E1203: {path}.id must be a string"
        )

    if resource_key == "locations":
        _validate_location_spatial(path=path, resource=resource)

    quantity = resource.get("quantity")
    if quantity is None:
        return
    if not isinstance(quantity, dict):
        raise ValidationError(
            f"E1204: {path}.quantity must be an object"
        )

    _validate_resource_quantity(path=path, quantity=quantity)


def _validate_location_spatial(path: str, resource: dict[str, Any]) -> None:
    spatial = _extract_location_spatial(resource)
    if spatial is None:
        return

    if not isinstance(spatial, dict):
        raise ValidationError(
            f"E1214: {path}.metadata.spatial must be an object"
        )

    x = spatial.get("x")
    y = spatial.get("y")
    if not _is_number(x) or not _is_number(y):
        raise ValidationError(
            f"E1215: {path}.metadata.spatial must include numeric x and y"
        )

    unit = spatial.get("unit")
    if unit is not None and (not isinstance(unit, str) or unit.strip().lower() not in _SPATIAL_UNITS):
        raise ValidationError(
            f"E1216: {path}.metadata.spatial.unit must be one of {sorted(_SPATIAL_UNITS)}"
        )


def _extract_location_spatial(resource: dict[str, Any]) -> dict[str, Any] | None:
    metadata = resource.get("metadata")
    if isinstance(metadata, dict) and "spatial" in metadata:
        return metadata.get("spatial")

    if "x" in resource or "y" in resource:
        return {
            "x": resource.get("x"),
            "y": resource.get("y"),
            "unit": resource.get("unit"),
        }

    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_resource_quantity(path: str, quantity: dict[str, Any]) -> None:
    kind = quantity.get("kind")
    if kind not in {"count", "measure"}:
        raise ValidationError(
            f"E1205: {path}.quantity.kind must be 'count' or 'measure'"
        )

    if kind == "count":
        _validate_count_quantity(path=path, quantity=quantity)
        return

    _validate_measure_quantity(path=path, quantity=quantity)


def _validate_count_quantity(path: str, quantity: dict[str, Any]) -> None:
    value = quantity.get("value")
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValidationError(
            f"E1206: {path}.quantity.value must be an integer >= 1 for kind=count"
        )

    unit = quantity.get("unit")
    if unit is not None and (not isinstance(unit, str) or unit.strip().lower() != "each"):
        raise ValidationError(
            f"E1207: {path}.quantity.unit must be 'each' for kind=count"
        )

    qualifier = quantity.get("qualifier")
    if qualifier is not None and not isinstance(qualifier, str):
        raise ValidationError(
            f"E1208: {path}.quantity.qualifier must be a string"
        )


def _validate_measure_quantity(path: str, quantity: dict[str, Any]) -> None:
    value = quantity.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) <= 0:
        raise ValidationError(
            f"E1209: {path}.quantity.value must be a number > 0 for kind=measure"
        )

    unit = quantity.get("unit")
    if not isinstance(unit, str) or unit.strip().lower() not in _MEASURE_UNITS:
        raise ValidationError(
            f"E1210: {path}.quantity.unit must be one of {sorted(_MEASURE_UNITS)} for kind=measure"
        )

    canonical_value = quantity.get("canonical_value")
    canonical_unit = quantity.get("canonical_unit")
    if (canonical_value is None) != (canonical_unit is None):
        raise ValidationError(
            f"E1211: {path}.quantity canonical_value and canonical_unit must be provided together"
        )
    if canonical_value is None:
        return

    _validate_canonical_quantity(path=path, canonical_value=canonical_value, canonical_unit=canonical_unit)


def _validate_canonical_quantity(path: str, canonical_value: Any, canonical_unit: Any) -> None:
    if not isinstance(canonical_value, (int, float)) or isinstance(canonical_value, bool) or float(canonical_value) <= 0:
        raise ValidationError(
            f"E1212: {path}.quantity.canonical_value must be a number > 0"
        )
    if not isinstance(canonical_unit, str) or canonical_unit.strip().lower() not in _MEASURE_UNITS:
        raise ValidationError(
            f"E1213: {path}.quantity.canonical_unit must be one of {sorted(_MEASURE_UNITS)}"
        )


def _validate_node_value_class(obj: IR) -> None:
    valid_values = {vc.value for vc in ProcessValueClass}
    for node in obj.nodes:
        metadata = _extract_node_metadata(node)
        raw = metadata.get("value_class")
        if raw is None:
            continue
        if not isinstance(raw, str) or raw not in valid_values:
            raise ValidationError(
                f"E1320: node '{node.id}' metadata.value_class '{raw}' "
                f"must be one of {sorted(valid_values)}"
            )


def _extract_node_metadata(node: Any) -> dict[str, Any]:
    attrs = getattr(node, "attrs", None)
    if not isinstance(attrs, dict):
        return {}
    metadata = attrs.get("metadata")
    if isinstance(metadata, dict):
        return metadata
    return {}


def validate_against_schema(ir: IR) -> None:
    """Validate an `IR` instance against the JSON schema file.

    Raises `ValidationError` on schema validation failure.
    """
    schema_path = _locate_schema("flo_ir.json")

    if not _JSONSCHEMA_AVAILABLE:
        raise RuntimeError("jsonschema package not available for schema validation")

    with schema_path.open("r", encoding="utf-8") as fh:
        schema = json.load(fh)

    instance = ir_to_schema_dict(ir)
    validate_fn = getattr(jsonschema, "validate", None)
    if not callable(validate_fn):
        raise RuntimeError("jsonschema.validate is not available for schema validation")

    try:
        validate_fn(instance=instance, schema=schema)
    except Exception as e:
        raise ValidationError(f"schema validation failed: {e}")


def ensure_schema_aligned(ir: object) -> None:
    """Ensure the given IR is valid against the schema export contract."""
    if not isinstance(ir, IR):
        raise ValidationError("compiled output is not an IR instance")

    validate_against_schema(ir)


def _locate_schema(name: str) -> Path:
    candidate = Path(__file__).resolve().parents[3] / "schema" / name
    if candidate.exists():
        return candidate
    alt = Path(__file__).resolve().parents[4] / "schema" / name
    if alt.exists():
        return alt
    raise ValidationError(f"schema file not found: {candidate}")
