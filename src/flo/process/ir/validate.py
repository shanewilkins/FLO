"""Validation helpers for the FLO IR types (now under compiler.ir)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, TypeGuard

from flo.errors import ValidationError
from flo.process.contracts import (
    MEASUREMENT_ADAPTER,
    HandoffRelation,
    MeasurementProfile,
    ReworkRelation,
)
from flo.process.durations import duration_seconds
from flo.process.field_applicability import NODE_FIELDS, inapplicable_fields
from flo.process.measurements import selected_result
from flo.process.units import (
    MEASURE_UNITS,
    SPATIAL_UNITS,
    convert_measure,
)

from ._graph_utils import build_adjacency_maps, traverse
from .enums import VALUE_CLASS_NODE_KINDS, ProcessValueClass
from .models import IR
from .schema_projection import ir_to_schema_dict
from .validate_relations import (
    validate_context_relations,
    validate_item_relations,
    validate_resource_relations,
)
from .validate_render_intent import validate_render_intent
from .validate_structure import validate_parallel_structure
from .validate_subprocess import validate_subprocess_metadata
from .validate_waits import validate_wait_measurements

_QUANTITY_REL_TOL = 1e-9


class _LocatedValidationError(ValidationError):
    """Retain a typed field path for source-boundary enrichment."""

    def __init__(self, message: str, location: tuple[str | int, ...]) -> None:
        super().__init__(message)
        self.location = location


class _QuantityValidationError(_LocatedValidationError):
    """Carry a quantity field location for source-boundary enrichment."""

    def __init__(self, message: str, field: str) -> None:
        super().__init__(message, (field,))


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

    _validate_node_applicability(obj)
    _validate_process_measurement(obj)
    _validate_node_measurements(obj)
    _validate_value_class(obj)
    _validate_start_nodes(obj)
    _validate_edge_resolution(obj, ids)
    incoming_counts, outgoing_counts = _build_edge_degree_maps(obj, ids)
    _validate_branch_points(obj, outgoing_counts)
    _validate_queue_nodes(obj, incoming_counts, outgoing_counts)
    _validate_node_io_lists(obj)
    validate_wait_measurements(obj)
    validate_subprocess_metadata(obj)
    _validate_edge_metadata(obj)
    _validate_process_resources(obj)
    validate_context_relations(obj)
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


def _validate_node_io_lists(obj: IR) -> None:
    for node in obj.nodes:
        for field in (
            "consumes",
            "produces",
            "performed_by",
            "uses",
        ):
            value = getattr(node, field)

            if not isinstance(value, list):
                raise ValidationError(f"E1310: node '{node.id}' {field} must be a list")

            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    raise ValidationError(
                        f"E1311: node '{node.id}' {field}[{index}] must be a non-empty string"
                    )


def _validate_node_applicability(obj: IR) -> None:
    for node in obj.nodes:
        semantic = set().union(*NODE_FIELDS.values()) - {
            "id",
            "kind",
            "outcomes",
            "routes",
            "branch",
        }
        supplied = {
            field
            for field in semantic
            if getattr(node, field, None) is not None
            and getattr(node, field, None) != []
        }
        supplied |= {
            field for field in ("branch", "outcomes", "routes") if field in node.attrs
        }
        forbidden = inapplicable_fields(node.type, supplied)
        if forbidden:
            raise ValidationError(
                f"E1508: node '{node.id}' {', '.join(sorted(forbidden))} cannot be declared on kind '{node.type}'"
            )


def _validate_process_measurement(obj: IR) -> None:
    if obj.lead_time is None:
        return
    try:
        MeasurementProfile.model_validate(obj.lead_time)
    except Exception as exc:
        raise _LocatedValidationError(
            "E1301: process lead_time must be a valid measurement profile",
            ("process", "lead_time"),
        ) from exc
    _validate_selected_durations(
        obj.lead_time,
        context="process lead_time",
        location=("process", "lead_time"),
    )


def _validate_selected_durations(
    measurement: object, *, context: str, location: tuple[str | int, ...] = ()
) -> None:
    for selector in ("analysis_input", "primary"):
        result = selected_result(measurement, selector)
        if result is not None and duration_seconds(result) is None:
            raise _LocatedValidationError(
                f"E1303: {context} {selector} must be a valid duration",
                location,
            )


def _validate_node_measurements(obj: IR) -> None:
    for node in obj.nodes:
        node_type = node.type.strip().lower()
        if node_type in {
            "start",
            "end",
            "decision",
            "branch",
            "parallel_split",
            "parallel_join",
        } and any(
            getattr(node, field) is not None
            for field in (
                "cycle_time",
                "wait_time",
                "changeover_time",
                "value_class",
            )
        ):
            raise ValidationError(
                f"E1508: control node '{node.id}' cannot declare operational measurements"
            )
        if node_type not in {"task", "system_task", "subprocess"} and (
            node.cycle_time is not None or node.changeover_time is not None
        ):
            raise ValidationError(
                f"E1508: node '{node.id}' cycle_time and changeover_time belong on work steps"
            )
        for field in ("cycle_time", "wait_time", "changeover_time"):
            value = getattr(node, field)
            if value is None:
                continue
            try:
                MEASUREMENT_ADAPTER.validate_python(value)
            except Exception as exc:
                raise ValidationError(
                    f"E1301: node '{node.id}' {field} must be a valid measurement profile or reference"
                ) from exc
            _validate_selected_durations(value, context=f"node '{node.id}' {field}")


def _validate_process_resources(obj: IR) -> None:
    metadata = obj.process_metadata or {}
    retired = {
        "items",
        "resources",
        "locations",
        "materials",
        "equipment",
        "workers",
    } & metadata.keys()
    if retired:
        raise ValidationError(
            f"E1201: collections must use first-class process fields, not process_metadata: {', '.join(sorted(retired))}"
        )
    collections = {
        key: getattr(obj, key, None) for key in ("items", "resources", "locations")
    }
    for resource_key, resources in collections.items():
        if resources is None:
            continue
        _validate_resource_collection(
            resource_key=resource_key,
            collection=resources,
            path=resource_key,
            seen_ids=set(),
            location=(resource_key,),
        )


def _validate_resource_collection(
    resource_key: str,
    collection: Any,
    path: str,
    seen_ids: set[str],
    location: tuple[str | int, ...],
) -> None:
    try:
        _validate_resource_collection_contents(
            resource_key, collection, path, seen_ids, location
        )
    except _LocatedValidationError:
        raise
    except ValidationError as exc:
        raise _LocatedValidationError(str(exc), location) from exc


def _validate_resource_collection_contents(
    resource_key: str,
    collection: Any,
    path: str,
    seen_ids: set[str],
    location: tuple[str | int, ...],
) -> None:
    if isinstance(collection, list):
        for index, resource in enumerate(collection):
            try:
                _validate_resource_item(
                    resource_key=resource_key,
                    path=f"{path}[{index}]",
                    resource=resource,
                    seen_ids=seen_ids,
                    location=(*location, index),
                )
            except _LocatedValidationError:
                raise
            except ValidationError as exc:
                raise _LocatedValidationError(str(exc), (*location, index)) from exc
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
                location=(*location, group_name),
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
    location: tuple[str | int, ...],
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

    try:
        _validate_resource_quantity(path=path, quantity=quantity)
    except _QuantityValidationError as exc:
        exc.location = (*location, "quantity", *exc.location)
        raise


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
            f"E1215: {path}.metadata.spatial must include finite numeric x and y"
        )

    unit = spatial.get("unit")
    if unit is not None and (
        not isinstance(unit, str) or unit.strip().lower() not in SPATIAL_UNITS
    ):
        raise ValidationError(
            f"E1216: {path}.metadata.spatial.unit must be one of {sorted(SPATIAL_UNITS)}"
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


def _is_number(value: Any) -> TypeGuard[int | float]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


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
    if not _is_number(value) or value <= 0:
        raise ValidationError(
            f"E1209: {path}.quantity.value must be a finite number > 0 for kind=measure"
        )

    unit = quantity.get("unit")
    if not isinstance(unit, str) or unit.strip().lower() not in MEASURE_UNITS:
        raise ValidationError(
            f"E1210: {path}.quantity.unit must be one of {sorted(MEASURE_UNITS)} for kind=measure"
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
        path=path,
        canonical_value=canonical_value,
        canonical_unit=canonical_unit,
        value=value,
        unit=unit,
    )


def _validate_canonical_quantity(
    path: str,
    canonical_value: Any,
    canonical_unit: Any,
    *,
    value: float,
    unit: str,
) -> None:
    if not _is_number(canonical_value) or canonical_value <= 0:
        raise ValidationError(
            f"E1212: {path}.quantity.canonical_value must be a finite number > 0"
        )
    if (
        not isinstance(canonical_unit, str)
        or canonical_unit.strip().lower() not in MEASURE_UNITS
    ):
        raise ValidationError(
            f"E1213: {path}.quantity.canonical_unit must be one of {sorted(MEASURE_UNITS)}"
        )
    try:
        equivalent = convert_measure(float(value), unit, canonical_unit)
    except ValueError as exc:
        raise _QuantityValidationError(
            f"E1222: {path}.quantity.canonical_unit must have the same dimension as unit '{unit}'",
            "canonical_unit",
        ) from exc
    if not math.isfinite(equivalent) or equivalent <= 0:
        raise _QuantityValidationError(
            f"E1224: {path}.quantity.canonical_value conversion must remain finite and > 0 in '{canonical_unit}'",
            "canonical_value",
        )
    if not math.isclose(
        equivalent, canonical_value, rel_tol=_QUANTITY_REL_TOL, abs_tol=0
    ):
        raise _QuantityValidationError(
            f"E1223: {path}.quantity.canonical_value must represent the same amount as {value} {unit} "
            f"({equivalent:g} {canonical_unit}; relative tolerance {_QUANTITY_REL_TOL:g}, absolute tolerance 0)",
            "canonical_value",
        )


def _validate_value_class(obj: IR) -> None:
    valid_values = {vc.value for vc in ProcessValueClass}
    for node in obj.nodes:
        raw = node.value_class
        if raw is None:
            continue
        node_kind = node.type.strip().lower()
        if node_kind not in VALUE_CLASS_NODE_KINDS:
            raise ValidationError(
                f"E1322: node '{node.id}' of kind '{node.type}' cannot declare "
                "value_class; value_class is valid only on "
                f"{sorted(VALUE_CLASS_NODE_KINDS)}"
            )
        if not isinstance(raw, str) or raw not in valid_values:
            raise ValidationError(
                f"E1320: node '{node.id}' value_class '{raw}' "
                f"must be one of {sorted(valid_values)}"
            )


def _validate_edge_metadata(obj: IR) -> None:
    for edge in obj.edges:
        for field, contract in (
            ("handoff", HandoffRelation),
            ("rework", ReworkRelation),
        ):
            value = getattr(edge, field)
            if value is None:
                continue
            try:
                contract.model_validate(value)
            except Exception as exc:
                raise ValidationError(
                    f"E1401: edge '{edge.source}' -> '{edge.target}' {field} must be a valid structured relation"
                ) from exc


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
