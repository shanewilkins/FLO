"""Subprocess hierarchy validation helpers for FLO IR."""

from __future__ import annotations

from typing import Any

from flo.schema.subprocess_refs import iter_subprocess_detail_map_reference_values

from .models import IR
from flo.services.errors import ValidationError


def validate_subprocess_metadata(obj: IR) -> None:
    """Validate subprocess hierarchy links and detail-map reference metadata."""
    nodes_by_id = {node.id: node for node in obj.nodes}
    subprocess_ids = {
        node.id for node in obj.nodes if (node.type or "").lower() == "subprocess"
    }

    for node in obj.nodes:
        parent_id = extract_subprocess_parent(node)
        if parent_id is None:
            continue
        if parent_id not in nodes_by_id:
            raise ValidationError(
                f"E1330: node '{node.id}' subprocess_parent '{parent_id}' must resolve to an existing node"
            )
        if parent_id not in subprocess_ids:
            raise ValidationError(
                f"E1331: node '{node.id}' subprocess_parent '{parent_id}' must refer to a subprocess node"
            )
        if parent_id == node.id:
            raise ValidationError(
                f"E1332: node '{node.id}' subprocess_parent cannot refer to itself"
            )

    _validate_subprocess_parent_cycles(obj=obj, nodes_by_id=nodes_by_id)

    for node in obj.nodes:
        if (node.type or "").lower() != "subprocess":
            continue
        metadata = _extract_node_metadata(node)
        for key, value in iter_subprocess_detail_map_reference_values(metadata):
            if not value:
                raise ValidationError(
                    f"E1333: node '{node.id}' metadata.{key} must be a non-empty string"
                )


def _validate_subprocess_parent_cycles(*, obj: IR, nodes_by_id: dict[str, Any]) -> None:
    for node in obj.nodes:
        seen: set[str] = set()
        current = node
        while True:
            parent_id = extract_subprocess_parent(current)
            if parent_id is None:
                break
            if parent_id in seen:
                raise ValidationError(
                    f"E1334: node '{node.id}' participates in a circular subprocess_parent chain"
                )
            seen.add(parent_id)
            parent = nodes_by_id.get(parent_id)
            if parent is None:
                break
            current = parent


def extract_subprocess_parent(node: Any) -> str | None:
    """Return normalized subprocess_parent for a node, if present."""
    attrs = getattr(node, "attrs", None)
    if not isinstance(attrs, dict):
        return None
    value = attrs.get("subprocess_parent")
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _extract_node_metadata(node: Any) -> dict[str, Any]:
    attrs = getattr(node, "attrs", None)
    if not isinstance(attrs, dict):
        return {}
    metadata = attrs.get("metadata")
    if isinstance(metadata, dict):
        return metadata
    return {}
