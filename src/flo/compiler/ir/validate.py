"""Validation helpers for the FLO IR types (now under compiler.ir)."""
from __future__ import annotations

from typing import Any

from .models import IR
from flo.services.errors import ValidationError
from flo.export import ir_to_schema_dict
from pathlib import Path
import json

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
