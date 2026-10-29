"""Canonical IR validation orchestration."""

from typing import Any

from flo.errors import ValidationError
from flo.process.field_applicability import NODE_FIELDS, inapplicable_fields

from ._boundary_validation import validate_edge_relations, validate_node_relations
from .models import IR
from .validate_entities import _validate_process_resources
from .validate_graph import (
    _build_edge_degree_maps,
    _validate_ambiguous_fan_out,
    _validate_boundary_edges,
    _validate_branch_points,
    _validate_edge_resolution,
    _validate_global_reachability,
    _validate_node_connectivity,
    _validate_queue_nodes,
    _validate_start_nodes,
)
from .validate_measurements import (
    _validate_node_measurements,
    _validate_process_measurement,
)
from .validate_relations import (
    validate_context_relations,
    validate_item_relations,
    validate_resource_relations,
)

# Public validation entrypoints retain their documented import location.
from .validate_schema import ensure_schema_aligned as ensure_schema_aligned
from .validate_schema import validate_against_schema as validate_against_schema
from .validate_structure import validate_parallel_structure
from .validate_subprocess import validate_subprocess_metadata
from .validate_waits import validate_wait_measurements


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
    _validate_start_nodes(obj)
    _validate_edge_resolution(obj, ids)
    incoming_counts, outgoing_counts = _build_edge_degree_maps(obj, ids)
    _validate_branch_points(obj, outgoing_counts)
    _validate_queue_nodes(obj, incoming_counts, outgoing_counts)
    validate_node_relations(obj)
    validate_wait_measurements(obj)
    validate_subprocess_metadata(obj)
    validate_edge_relations(obj)
    _validate_process_resources(obj)
    validate_context_relations(obj)
    validate_item_relations(obj)
    validate_resource_relations(obj)
    validate_parallel_structure(obj, incoming_counts, outgoing_counts)
    _validate_node_connectivity(obj, incoming_counts, outgoing_counts)
    _validate_global_reachability(obj)
    _validate_boundary_edges(obj)
    _validate_ambiguous_fan_out(obj, outgoing_counts)


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
        if node.branch is not None:
            supplied.add("branch")
        forbidden = inapplicable_fields(node.type, supplied)
        if forbidden:
            raise ValidationError(
                f"E1508: node '{node.id}' {', '.join(sorted(forbidden))} cannot be declared on kind '{node.type}'"
            )
