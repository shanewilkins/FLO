"""Validation helpers for item and resource relation semantics in FLO IR."""

from __future__ import annotations

from typing import Any

from .models import IR
from flo.errors import ValidationError


def validate_item_relations(obj: IR) -> None:
    """Validate consumes/produces item references against declared process items."""
    process_metadata = getattr(obj, "process_metadata", None)
    if not isinstance(process_metadata, dict):
        return

    items_collection = process_metadata.get("items")
    declared_items = _collect_declared_kinds(items_collection)
    if not declared_items:
        return

    for node in obj.nodes:
        attrs = getattr(node, "attrs", None)
        for relation in ("consumes", "produces"):
            relation_values = _extract_relation_values(attrs, relation)
            if relation_values is None:
                continue
            for item_ref in relation_values:
                if isinstance(item_ref, str) and item_ref in declared_items:
                    continue
                raise ValidationError(
                    f"E1312: node '{node.id}' {relation} item '{item_ref}' must reference a declared process item id"
                )


def validate_resource_relations(obj: IR) -> None:
    """Validate performed_by/uses references against declared typed resources."""
    process_metadata = getattr(obj, "process_metadata", None)
    if not isinstance(process_metadata, dict):
        return

    resources_collection = process_metadata.get("resources")
    declared_resources = _collect_declared_kinds(resources_collection)
    if not declared_resources:
        return

    relation_expectations = {
        "performed_by": "person",
        "uses": "equipment",
    }

    for node in obj.nodes:
        attrs = getattr(node, "attrs", None)
        for relation, expected_kind in relation_expectations.items():
            relation_values = _extract_relation_values(attrs, relation)
            if relation_values is None:
                continue
            for resource_ref in relation_values:
                if (
                    not isinstance(resource_ref, str)
                    or resource_ref not in declared_resources
                ):
                    raise ValidationError(
                        f"E1313: node '{node.id}' {relation} resource '{resource_ref}' must reference a declared process resource id"
                    )

                resource_kind = declared_resources.get(resource_ref)
                if resource_kind is not None and resource_kind != expected_kind:
                    raise ValidationError(
                        f"E1314: node '{node.id}' {relation} resource '{resource_ref}' must reference kind '{expected_kind}'"
                    )


def _extract_relation_values(attrs: Any, relation: str) -> list[Any] | None:
    if not isinstance(attrs, dict):
        return None
    value = attrs.get(relation)
    if isinstance(value, list):
        return value
    return None


def _collect_declared_kinds(collection: Any) -> dict[str, str | None]:
    ids: dict[str, str | None] = {}

    if isinstance(collection, list):
        for entry in collection:
            if not isinstance(entry, dict):
                continue
            entry_id = entry.get("id")
            if isinstance(entry_id, str) and entry_id.strip():
                entry_kind = entry.get("kind")
                ids[entry_id] = entry_kind if isinstance(entry_kind, str) else None
        return ids

    if not isinstance(collection, dict):
        return ids

    for group_name, nested in collection.items():
        if group_name == "name":
            continue
        ids.update(_collect_declared_kinds(nested))

    return ids
