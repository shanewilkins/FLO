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
