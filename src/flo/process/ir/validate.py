"""Validation helpers for the FLO IR types (now under compiler.ir)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flo.errors import ValidationError

from ._graph_utils import build_adjacency_maps, traverse
from .enums import ProcessValueClass
from .metadata import extract_node_metadata
from .models import IR
from .schema_projection import ir_to_schema_dict
from .validate_relations import validate_item_relations, validate_resource_relations
from .validate_render_intent import validate_render_intent
from .validate_structure import validate_parallel_structure
from .validate_subprocess import validate_subprocess_metadata

_MEASURE_UNITS = {"mg", "g", "kg", "ml", "l", "mm", "cm", "m"}
_TIME_UNITS = {"s", "m", "min", "hr", "d"}
_SPATIAL_UNITS = {"mm", "cm", "m", "in", "ft"}

try:
    import jsonschema

    _JSONSCHEMA_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    jsonschema = None
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
    _validate_branch_points(obj, outgoing_counts)
    _validate_queue_nodes(obj, incoming_counts, outgoing_counts)
    _validate_queue_wait_time_semantics(obj)
    _validate_wait_measurement_links(obj)
    _validate_node_io_lists(obj)
    _validate_node_time_metadata(obj)
    _validate_node_value_class(obj)
    validate_subprocess_metadata(obj)
    _validate_edge_metadata(obj)
    _validate_process_resources(obj)
    validate_item_relations(obj)
    validate_resource_relations(obj)
    validate_parallel_structure(obj, incoming_counts, outgoing_counts)
    _validate_node_connectivity(obj, incoming_counts, outgoing_counts)
    _validate_global_reachability(obj)
    _validate_boundary_edges(obj)
    _validate_ambiguous_fan_out(obj, outgoing_counts)


def _validate_start_nodes(obj: IR) -> None:
    start_nodes = [n for n in obj.nodes if (n.type or "").lower() == "start"]
    if len(start_nodes) != 1:
        raise ValidationError("E1003: IR must contain exactly one start node")


def _validate_edge_resolution(obj: IR, ids: list[str]) -> None:
    known_ids = set(ids)
    for edge in obj.edges:
        if edge.source not in known_ids or edge.target not in known_ids:
            raise ValidationError(
                f"E1004: edge endpoint unresolved: {edge.source} -> {edge.target}"
            )


def _build_edge_degree_maps(
    obj: IR, ids: list[str]
) -> tuple[dict[str, int], dict[str, int]]:
    known_ids = set(ids)
    incoming_counts: dict[str, int] = dict.fromkeys(known_ids, 0)
    outgoing_counts: dict[str, int] = dict.fromkeys(known_ids, 0)
    for edge in obj.edges:
        if edge.target in incoming_counts:
            incoming_counts[edge.target] += 1
        if edge.source in outgoing_counts:
            outgoing_counts[edge.source] += 1
    return incoming_counts, outgoing_counts


def _validate_branch_points(obj: IR, outgoing_counts: dict[str, int]) -> None:
    node_types = {node.id: (node.type or "").lower() for node in obj.nodes}
    for node in obj.nodes:
        node_type = node_types[node.id]
        outgoing_count = outgoing_counts.get(node.id, 0)
        if node_type == "decision" and outgoing_count < 2:
            raise ValidationError(
                f"E1005: decision node '{node.id}' must have at least two outgoing edges"
            )
        if node_type == "decision":
            _validate_decision_edges(obj=obj, node_id=node.id)

        if node_type == "branch":
            if outgoing_count < 2:
                raise ValidationError(
                    f"E1026: branch node '{node.id}' must have at least two outgoing edges"
                )
            _validate_branch_node(node_id=node.id, attrs=node.attrs)
            _validate_branch_edges(obj=obj, node_id=node.id)

    for edge in obj.edges:
        outcome = (edge.outcome or "").strip()
        if outcome and node_types.get(edge.source) != "decision":
            raise ValidationError(
                f"E1022: edge '{edge.source}' -> '{edge.target}' declares outcome "
                f"'{outcome}', but source '{edge.source}' is not a decision. "
                "Remove the outcome or change the source to a decision."
            )
        route = (edge.route or "").strip()
        if route and node_types.get(edge.source) != "branch":
            raise ValidationError(
                f"E1027: edge '{edge.source}' -> '{edge.target}' declares route "
                f"'{route}', but source '{edge.source}' is not a branch. "
                "Remove the route or change the source to a branch."
            )


def _validate_decision_edges(*, obj: IR, node_id: str) -> None:
    seen_outcomes: set[str] = set()
    for edge in (edge for edge in obj.edges if edge.source == node_id):
        outcome = (edge.outcome or "").strip()
        if not outcome:
            raise ValidationError(
                f"E1020: decision '{node_id}' has outgoing edge "
                f"'{edge.source}' -> '{edge.target}' without an outcome. "
                "Add a non-empty outcome to that transition or declare it "
                "in the decision's outcomes."
            )
        normalized_outcome = outcome.casefold()
        if normalized_outcome in seen_outcomes:
            raise ValidationError(
                f"E1021: decision '{node_id}' uses outcome '{outcome}' more than "
                "once. Give each outgoing branch a unique outcome."
            )
        seen_outcomes.add(normalized_outcome)
        if edge.route:
            raise ValidationError(
                f"E1028: decision edge '{edge.source}' -> '{edge.target}' declares "
                "a route. Decision edges use outcome, not route."
            )


def _validate_branch_node(*, node_id: str, attrs: Any) -> None:
    config = attrs.get("branch") if isinstance(attrs, dict) else None
    if not isinstance(config, dict):
        raise ValidationError(
            f"E1029: branch node '{node_id}' must declare branch.mode."
        )
    mode = config.get("mode")
    allowed_modes = {"dispatch", "probabilistic", "external", "unspecified"}
    if mode not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        raise ValidationError(
            f"E1030: branch node '{node_id}' has invalid branch.mode '{mode}'. "
            f"Expected one of: {allowed}."
        )


def _validate_branch_edges(*, obj: IR, node_id: str) -> None:
    seen_routes: set[str] = set()
    for edge in (edge for edge in obj.edges if edge.source == node_id):
        if edge.outcome:
            raise ValidationError(
                f"E1031: branch edge '{edge.source}' -> '{edge.target}' declares "
                "an outcome. Generic branch edges use route, not outcome."
            )
        route = (edge.route or "").strip()
        if not route:
            continue
        normalized_route = route.casefold()
        if normalized_route in seen_routes:
            raise ValidationError(
                f"E1032: branch '{node_id}' uses route '{route}' more than once. "
                "Give each named route a unique name."
            )
        seen_routes.add(normalized_route)


def _validate_ambiguous_fan_out(obj: IR, outgoing_counts: dict[str, int]) -> None:
    branch_point_types = {"decision", "branch", "parallel_split"}
    for node in obj.nodes:
        node_type = (node.type or "").lower()
        outgoing_count = outgoing_counts.get(node.id, 0)
        if outgoing_count > 1 and node_type not in branch_point_types:
            raise ValidationError(
                f"E1025: node '{node.id}' has {outgoing_count} outgoing edges but "
                f"kind '{node_type}' is not a branch point. Change it to decision, "
                "branch, or parallel_split to declare how paths are selected."
            )


def _validate_queue_nodes(
    obj: IR, incoming_counts: dict[str, int], outgoing_counts: dict[str, int]
) -> None:
    for node in obj.nodes:
        if (node.type or "").lower() != "queue":
            continue

        metadata = extract_node_metadata(node)
        _validate_queue_metadata(node_id=node.id, metadata=metadata)

        if incoming_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1103: queue node '{node.id}' must have at least one incoming edge"
            )
        if outgoing_counts.get(node.id, 0) < 1:
            raise ValidationError(
                f"E1104: queue node '{node.id}' must have at least one outgoing edge"
            )


def _validate_queue_wait_time_semantics(obj: IR) -> None:
    """Enforce canonical queue and pre-task waiting field placement.

    - Queue nodes (kind: queue) may have wait_time (queue delays).
    - Work nodes may have wait_before but not the source-only wait_time alias.
    - Task nodes may have cycle_time and crossover_time (work duration and setup).
    - Queue nodes must NOT have wait_before, cycle_time, or crossover_time.
    """
    for node in obj.nodes:
        node_type = (node.type or "").lower()
        metadata = extract_node_metadata(node)

        if node_type == "queue":
            if "wait_before" in metadata:
                raise ValidationError(
                    f"E1504: queue node '{node.id}' has wait_before metadata. "
                    "Queues own wait_time; wait_before belongs on work nodes."
                )
            if "cycle_time" in metadata:
                raise ValidationError(
                    f"E1501: queue node '{node.id}' has cycle_time metadata. "
                    f"Queues represent delays only; use wait_time. "
                    f"Cycle time belongs on task nodes."
                )
            if (
                "crossover_time" in metadata
                or "transfer_time" in metadata
                or "changeover_time" in metadata
            ):
                raise ValidationError(
                    f"E1502: queue node '{node.id}' has crossover/transfer/changeover_time metadata. "
                    f"Queues represent delays only; use wait_time. "
                    f"Setup time belongs on task nodes."
                )
        elif node_type in {"task", "system_task", "subprocess"}:
            if "wait_time" in metadata:
                raise ValidationError(
                    f"E1503: {node_type} node '{node.id}' has wait_time metadata. "
                    "Canonical work-node metadata uses wait_before. Rename the "
                    "field, or compile authored FLO source so the compatibility "
                    "alias is normalized."
                )


def _validate_wait_measurement_links(obj: IR) -> None:
    nodes_by_id = {node.id: node for node in obj.nodes}
    task_waits_by_id: dict[str, str] = {}
    for node in obj.nodes:
        if (node.type or "").lower() not in {"task", "system_task", "subprocess"}:
            continue
        task_wait = extract_node_metadata(node).get("wait_before")
        if not isinstance(task_wait, dict):
            continue
        measurement_id = _measurement_id(task_wait)
        if measurement_id is None:
            continue
        previous_node_id = task_waits_by_id.get(measurement_id)
        if previous_node_id is not None:
            raise ValidationError(
                f"E1506: work nodes '{previous_node_id}' and '{node.id}' both "
                f"declare wait measurement_id '{measurement_id}'. Give each "
                "distinct wait measurement a unique ID."
            )
        task_waits_by_id[measurement_id] = node.id

    for node in obj.nodes:
        if (node.type or "").lower() != "queue":
            continue
        queue_wait = extract_node_metadata(node).get("wait_time")
        if not isinstance(queue_wait, dict):
            continue
        for measurement_ref in _measurement_refs(queue_wait):
            if measurement_ref not in task_waits_by_id:
                raise ValidationError(
                    f"E1507: queue '{node.id}' wait_time references unknown task "
                    f"wait measurement_id '{measurement_ref}'. Correct the reference "
                    "or add that measurement_id to a work-node wait_before."
                )

    for edge in obj.edges:
        source = nodes_by_id.get(edge.source)
        target = nodes_by_id.get(edge.target)
        if source is None or target is None:
            continue
        if (source.type or "").lower() != "queue" or (
            target.type or ""
        ).lower() not in {"task", "system_task", "subprocess"}:
            continue
        queue_wait = extract_node_metadata(source).get("wait_time")
        task_wait = extract_node_metadata(target).get("wait_before")
        if not isinstance(queue_wait, dict) or not isinstance(task_wait, dict):
            continue
        queue_measurement_id = _measurement_id(queue_wait)
        task_measurement_id = _measurement_id(task_wait)
        queue_measurement_refs = _measurement_refs(queue_wait)
        linked = task_measurement_id is not None and (
            queue_measurement_id == task_measurement_id
            or task_measurement_id in queue_measurement_refs
        )
        independently_identified = task_measurement_id is not None and (
            queue_measurement_id is not None or bool(queue_measurement_refs)
        )
        if not linked and not independently_identified:
            raise ValidationError(
                f"E1505: queue '{source.id}' wait_time and work node '{target.id}' "
                "wait_before describe the same queue-to-work boundary without a "
                "clear measurement relationship. Link a repeated measurement, give "
                "independent measurements distinct non-empty measurement_id values, or "
                "keep the measurement on only one node."
            )


def _measurement_id(duration: dict[str, Any]) -> str | None:
    value = duration.get("measurement_id")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _measurement_refs(duration: dict[str, Any]) -> tuple[str, ...]:
    value = duration.get("measurement_refs")
    if not isinstance(value, list):
        return ()
    return tuple(
        reference.strip()
        for reference in value
        if isinstance(reference, str) and reference.strip()
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
    adjacency, reverse_adjacency = build_adjacency_maps(
        node_ids=node_ids, edges=obj.edges
    )
    start_nodes = _collect_node_ids_by_type(obj=obj, node_type="start")
    end_nodes = _collect_node_ids_by_type(obj=obj, node_type="end")

    _ensure_end_nodes_present(end_nodes=end_nodes)
    _ensure_all_nodes_reachable_from_start(
        obj=obj, start_nodes=start_nodes, adjacency=adjacency
    )
    _ensure_all_nodes_can_reach_end(
        obj=obj, end_nodes=end_nodes, reverse_adjacency=reverse_adjacency
    )


def _validate_boundary_edges(obj: IR) -> None:
    node_types = {node.id: (node.type or "").lower() for node in obj.nodes}
    for edge in obj.edges:
        if node_types.get(edge.target) == "start":
            raise ValidationError(
                f"E1023: edge '{edge.source}' -> '{edge.target}' enters start node "
                f"'{edge.target}'. Start is the process entry boundary; target a "
                "process step instead."
            )
        if node_types.get(edge.source) == "end":
            raise ValidationError(
                f"E1024: edge '{edge.source}' -> '{edge.target}' leaves end node "
                f"'{edge.source}'. End is a process termination boundary; remove "
                "the transition or change its source."
            )


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
    reachable_from_start = traverse(start_nodes, adjacency)
    for node in obj.nodes:
        if node.id not in reachable_from_start:
            raise ValidationError(f"E1008: node '{node.id}' is unreachable from start")


def _ensure_all_nodes_can_reach_end(
    obj: IR,
    end_nodes: list[str],
    reverse_adjacency: dict[str, set[str]],
) -> None:
    can_reach_end = traverse(end_nodes, reverse_adjacency)
    for node in obj.nodes:
        if node.id not in can_reach_end:
            raise ValidationError(f"E1009: node '{node.id}' cannot reach any end node")


def _validate_queue_metadata(node_id: str, metadata: dict[str, Any]) -> None:
    # Queue nodes may have optional queue_policy for advanced queueing models.
    # For basic use (SPPM, VSM), queue_policy is not required.
    # All other fields are validated per type if present.

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

        for field in (
            "inputs",
            "outputs",
            "consumes",
            "produces",
            "performed_by",
            "uses",
        ):
            value = attrs.get(field)
            if value is None:
                continue

            if not isinstance(value, list):
                raise ValidationError(f"E1310: node '{node.id}' {field} must be a list")

            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    raise ValidationError(
                        f"E1311: node '{node.id}' {field}[{index}] must be a non-empty string"
                    )


def _validate_node_time_metadata(obj: IR) -> None:
    for node in obj.nodes:
        metadata = extract_node_metadata(node)
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

    return normalized in {"time", "duration", "wait_before"} or normalized.endswith(
        ("_time", "_duration")
    )


def _validate_node_time_metadata_value(node_id: str, key: str, value: Any) -> None:
    path = f"node '{node_id}' metadata.{key}"

    if not isinstance(value, dict):
        raise ValidationError(
            f"E1301: {path} must be an object with 'value' and 'unit'"
        )

    duration_value = value.get("value")
    if (
        not isinstance(duration_value, (int, float))
        or isinstance(duration_value, bool)
        or float(duration_value) < 0
    ):
        raise ValidationError(f"E1302: {path}.value must be a number >= 0")

    unit = value.get("unit")
    if not isinstance(unit, str) or unit.strip().lower() not in _TIME_UNITS:
        raise ValidationError(
            f"E1303: {path}.unit must be one of {sorted(_TIME_UNITS)}"
        )

    measurement_id = value.get("measurement_id")
    if measurement_id is not None and (
        not isinstance(measurement_id, str) or not measurement_id.strip()
    ):
        raise ValidationError(
            f"E1304: {path}.measurement_id must be a non-empty string"
        )

    measurement_refs = value.get("measurement_refs")
    if measurement_refs is not None and (
        not isinstance(measurement_refs, list)
        or not measurement_refs
        or any(
            not isinstance(reference, str) or not reference.strip()
            for reference in measurement_refs
        )
        or len(set(measurement_refs)) != len(measurement_refs)
    ):
        raise ValidationError(
            f"E1305: {path}.measurement_refs must be a non-empty list of unique strings"
        )


def _validate_process_resources(obj: IR) -> None:
    process_metadata = getattr(obj, "process_metadata", None)
    metadata = process_metadata if isinstance(process_metadata, dict) else {}

    collections = {
        "items": getattr(obj, "items", None),
        "resources": getattr(obj, "resources", None),
        "locations": getattr(obj, "locations", None),
        "materials": metadata.get("materials"),
        "equipment": metadata.get("equipment"),
        "workers": metadata.get("workers"),
    }
    for resource_key, resources in collections.items():
        if resources is None:
            continue
        _validate_resource_collection(
            resource_key=resource_key,
            collection=resources,
            path=resource_key,
            seen_ids=set(),
        )


def _validate_resource_collection(
    resource_key: str,
    collection: Any,
    path: str,
    seen_ids: set[str],
) -> None:
    if isinstance(collection, list):
        for index, resource in enumerate(collection):
            _validate_resource_item(
                resource_key=resource_key,
                path=f"{path}[{index}]",
                resource=resource,
                seen_ids=seen_ids,
            )
        return

    if isinstance(collection, dict):
        group_label = collection.get("name")
        if "name" in collection and (
            not isinstance(group_label, str) or not group_label.strip()
        ):
            raise ValidationError(
                f"E1201: process metadata '{path}.name' must be a non-empty string"
            )

        child_items = [
            (group_name, nested_collection)
            for group_name, nested_collection in collection.items()
            if group_name != "name"
        ]
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
                seen_ids=seen_ids,
            )
        return

    raise ValidationError(
        f"E1201: process metadata '{path}' must be a list or grouped object"
    )


def _validate_resource_item(
    resource_key: str,
    path: str,
    resource: Any,
    seen_ids: set[str],
) -> None:
    if not isinstance(resource, dict):
        raise ValidationError(f"E1202: {path} must be an object")

    resource_id = resource.get("id")
    if not isinstance(resource_id, str) or not resource_id.strip():
        raise ValidationError(f"E1219: {path}.id must be a non-empty string")
    if resource_id in seen_ids:
        raise ValidationError(
            f"E1221: {path}.id duplicates declared {resource_key} id '{resource_id}'"
        )
    seen_ids.add(resource_id)

    resource_name = resource.get("name")
    if not isinstance(resource_name, str) or not resource_name.strip():
        raise ValidationError(f"E1220: {path}.name must be a non-empty string")

    resource_kind = resource.get("kind")
    if resource_key == "items" and resource_kind not in {"material", "information"}:
        raise ValidationError(f"E1217: {path}.kind must be 'material' or 'information'")
    if resource_key == "resources" and resource_kind not in {"person", "equipment"}:
        raise ValidationError(f"E1218: {path}.kind must be 'person' or 'equipment'")

    if resource_key == "locations":
        _validate_location_spatial(path=path, resource=resource)

    quantity = resource.get("quantity")
    if quantity is None:
        return
    if not isinstance(quantity, dict):
        raise ValidationError(f"E1204: {path}.quantity must be an object")

    _validate_resource_quantity(path=path, quantity=quantity)


def _validate_location_spatial(path: str, resource: dict[str, Any]) -> None:
    spatial = _extract_location_spatial(resource)
    if spatial is None:
        return

    if not isinstance(spatial, dict):
        raise ValidationError(f"E1214: {path}.metadata.spatial must be an object")

    x = spatial.get("x")
    y = spatial.get("y")
    if not _is_number(x) or not _is_number(y):
        raise ValidationError(
            f"E1215: {path}.metadata.spatial must include numeric x and y"
        )

    unit = spatial.get("unit")
    if unit is not None and (
        not isinstance(unit, str) or unit.strip().lower() not in _SPATIAL_UNITS
    ):
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
    if unit is not None and (
        not isinstance(unit, str) or unit.strip().lower() != "each"
    ):
        raise ValidationError(
            f"E1207: {path}.quantity.unit must be 'each' for kind=count"
        )

    qualifier = quantity.get("qualifier")
    if qualifier is not None and not isinstance(qualifier, str):
        raise ValidationError(f"E1208: {path}.quantity.qualifier must be a string")


def _validate_measure_quantity(path: str, quantity: dict[str, Any]) -> None:
    value = quantity.get("value")
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or float(value) <= 0
    ):
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

    _validate_canonical_quantity(
        path=path, canonical_value=canonical_value, canonical_unit=canonical_unit
    )


def _validate_canonical_quantity(
    path: str, canonical_value: Any, canonical_unit: Any
) -> None:
    if (
        not isinstance(canonical_value, (int, float))
        or isinstance(canonical_value, bool)
        or float(canonical_value) <= 0
    ):
        raise ValidationError(
            f"E1212: {path}.quantity.canonical_value must be a number > 0"
        )
    if (
        not isinstance(canonical_unit, str)
        or canonical_unit.strip().lower() not in _MEASURE_UNITS
    ):
        raise ValidationError(
            f"E1213: {path}.quantity.canonical_unit must be one of {sorted(_MEASURE_UNITS)}"
        )


def _validate_node_value_class(obj: IR) -> None:
    valid_values = {vc.value for vc in ProcessValueClass}
    for node in obj.nodes:
        metadata = extract_node_metadata(node)
        raw = metadata.get("value_class")
        if raw is None:
            continue
        if not isinstance(raw, str) or raw not in valid_values:
            raise ValidationError(
                f"E1320: node '{node.id}' metadata.value_class '{raw}' "
                f"must be one of {sorted(valid_values)}"
            )


def _validate_edge_metadata(obj: IR) -> None:
    for edge in obj.edges:
        edge_type = str(getattr(edge, "edge_type", "") or "").strip().lower()
        rework = getattr(edge, "rework", None)
        if (edge_type == "rework" and rework is False) or (
            edge_type and edge_type != "rework" and rework is True
        ):
            raise ValidationError(
                f"E1404: edge '{edge.source}' -> '{edge.target}' has conflicting "
                f"rework declarations edge_type={edge.edge_type!r} and "
                f"rework={rework!r}. Use edge_type: rework with rework: true, "
                "or omit both for ordinary flow."
            )

        handoff_value = getattr(edge, "handoff", None)
        if handoff_value is not None and not isinstance(handoff_value, bool):
            raise ValidationError(
                f"E1410: edge '{edge.source}' -> '{edge.target}' handoff must be boolean"
            )

        metadata = getattr(edge, "metadata", None)
        if not isinstance(metadata, dict) or not metadata:
            continue
        if (
            bool(getattr(edge, "rework", None))
            or str(getattr(edge, "edge_type", "") or "").lower() == "rework"
        ):
            _validate_rework_edge_metadata(edge=edge, metadata=metadata)


def _validate_rework_edge_metadata(*, edge: Any, metadata: dict[str, Any]) -> None:
    edge_path = f"edge '{edge.source}' -> '{edge.target}'"

    rate = metadata.get("rate")
    if rate is not None and (
        not isinstance(rate, (int, float))
        or isinstance(rate, bool)
        or not (0 <= float(rate) <= 1)
    ):
        raise ValidationError(
            f"E1401: {edge_path} metadata.rate must be a number between 0 and 1"
        )

    for key in ("reason", "frequency", "note"):
        value = metadata.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"E1402: {edge_path} metadata.{key} must be a non-empty string"
            )

    count = metadata.get("count")
    if count is not None:
        is_valid_number = (
            isinstance(count, (int, float))
            and not isinstance(count, bool)
            and float(count) > 0
        )
        is_valid_text = isinstance(count, str) and bool(count.strip())
        if not (is_valid_number or is_valid_text):
            raise ValidationError(
                f"E1403: {edge_path} metadata.count must be a positive number or non-empty string"
            )


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
    except Exception as exc:
        raise ValidationError(f"schema validation failed: {exc}") from exc


def ensure_schema_aligned(ir: object) -> None:
    """Ensure the given IR is valid against the schema export contract."""
    if not isinstance(ir, IR):
        raise ValidationError("compiled output is not an IR instance")

    validate_against_schema(ir)
    validate_render_intent(ir)


def _locate_schema(name: str) -> Path:
    here = Path(__file__).resolve()
    candidates = [
        # Preferred: packaged schema payload at flo/process/schema/*.json
        here.parents[1] / "schema" / name,
        # Local repo layout when running from source tree.
        here.parents[4] / "schema" / name,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise ValidationError(f"schema file not found: {candidates[0]}")
