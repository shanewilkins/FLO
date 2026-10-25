"""Adapter-facing normalization helpers for compilation.

This module owns adapter payload normalization concerns: process metadata,
source node extraction/flattening, and attribute normalization.
"""

from __future__ import annotations

from typing import Any

from flo.process.schema.render_metadata import (
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)

from .models import (
    BranchConfig,
    NamedPaths,
    SourceDocument,
    SourceShapeError,
    source_path,
    validate_source_shape,
)


def validate_adapter_contract(adapter: dict[str, Any]) -> SourceDocument:
    """Validate source shapes once, then check source-specific relationships."""
    document = validate_source_shape(SourceDocument, adapter)
    seen_ids: set[str] = set()
    _validate_step_entries(adapter["steps"], (), seen_ids)
    for path, entries in (
        (("lanes",), adapter.get("lanes")),
        (("process", "business_units"), adapter["process"].get("business_units")),
    ):
        ids = [entry["id"] for entry in entries or []]
        if len(set(ids)) != len(ids):
            raise SourceShapeError(f"duplicate {source_path(path)} id detected", path)
    return document


def _validate_step_entries(
    steps: list[dict], parent: tuple, seen_ids: set[str]
) -> None:
    for index, step in enumerate(steps):
        path = (*parent, "steps", index) if not parent else (*parent, index)
        step_id = step["id"]
        if step_id in seen_ids:
            raise SourceShapeError(
                f"duplicate step id '{step_id}' detected at {source_path(path)}",
                (*path, "id"),
            )
        seen_ids.add(step_id)
        kind = step["kind"]
        attrs = step.get("attrs") or {}
        effective = {**step, **attrs}
        _validate_named_paths(effective, path, kind, attrs)
        branch = effective.get("branch")
        branch_path = (
            (*path, "attrs", "branch") if "branch" in attrs else (*path, "branch")
        )
        if kind == "branch":
            validate_source_shape(BranchConfig, branch, branch_path)
        elif branch is not None:
            raise SourceShapeError(
                f"E0214: {source_path(path)}.branch is only valid for kind 'branch'",
                branch_path,
            )
        metadata = effective.get("metadata") or {}
        if (
            kind in {"task", "system_task", "subprocess"}
            and "wait_time" in metadata
            and "wait_before" in metadata
        ):
            raise SourceShapeError(
                f"E0219: {source_path(path)}.metadata declares both wait_time and wait_before. "
                "Use wait_before; task wait_time is only a source compatibility alias.",
                (*path, "attrs", "metadata")
                if "metadata" in attrs
                else (*path, "metadata"),
            )
        nested_key = "subnodes" if "subnodes" in step else "steps"
        if kind == "subprocess" and nested_key in step:
            _validate_step_entries(step[nested_key], (*path, nested_key), seen_ids)


def _validate_named_paths(step: dict, path: tuple, kind: str, attrs: dict) -> None:
    for field, owner, wrong_kind, duplicate in (
        ("outcomes", "decision", "E0201", "E0204"),
        ("routes", "branch", "E0211", "E0213"),
    ):
        if field not in step:
            continue
        location = (*path, "attrs", field) if field in attrs else (*path, field)
        if kind != owner:
            raise SourceShapeError(
                f"{wrong_kind}: {source_path(location)} is only valid for kind '{owner}'",
                location,
            )
        validate_source_shape(NamedPaths, step[field], location)
        names = [_normalized_outcome_name(name).casefold() for name in step[field]]
        if len(names) != len(set(names)):
            raise SourceShapeError(
                f"{duplicate}: {source_path(location)} contains duplicate branch names",
                location,
            )


def _normalized_outcome_name(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return value.strip()


def resolve_process_name(adapter: dict[str, Any]) -> str:
    """Resolve display/process name from adapter payload."""
    return adapter["process"]["id"]


def resolve_process_version(adapter: dict[str, Any]) -> int | str | None:
    """Resolve the authored process version without coercing its scalar type."""
    return adapter["process"].get("version")


def resolve_process_owner(adapter: dict[str, Any]) -> dict[str, Any] | None:
    """Return the authored process owner as first-class process context."""
    owner = adapter["process"].get("owner")
    return dict(owner) if owner is not None else None


def resolve_business_units(adapter: dict[str, Any]) -> list[dict[str, Any]]:
    """Return authored business units in declared order."""
    return [dict(unit) for unit in adapter["process"].get("business_units") or []]


def resolve_lanes(adapter: dict[str, Any]) -> list[dict[str, Any]]:
    """Return authored lane declarations in declared order."""
    return [dict(lane) for lane in adapter.get("lanes") or []]


def resolve_items(adapter: dict[str, Any]) -> Any:
    """Return the canonical item collection outside opaque metadata."""
    return _resolve_canonical_process_value(adapter, "items")


def resolve_resources(adapter: dict[str, Any]) -> Any:
    """Return the canonical resource collection outside opaque metadata."""
    return _resolve_canonical_process_value(adapter, "resources")


def resolve_locations(adapter: dict[str, Any]) -> Any:
    """Return the canonical location collection outside opaque metadata."""
    return _resolve_canonical_process_value(adapter, "locations")


def resolve_render_intent(adapter: dict[str, Any]) -> Any:
    """Return FLO-typed render intent outside opaque process metadata."""
    return adapter["process"].get("metadata", {}).get("render")


def resolve_process_metadata(adapter: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve normalized process metadata payload from adapter model."""
    process = adapter["process"]
    metadata = dict(process.get("metadata", {}))
    for typed_key in ("items", "resources", "locations", "render"):
        metadata.pop(typed_key, None)

    metadata.setdefault(PROCESS_METADATA_PROCESS_ID_KEY, process["id"])
    metadata.setdefault(PROCESS_METADATA_PROCESS_NAME_KEY, process["name"])

    for key in (
        "materials",
        "equipment",
        "workers",
    ):
        value = adapter.get(key)
        if not _is_resource_collection(value):
            value = process.get(key)
        if _is_resource_collection(value):
            metadata[key] = value

    return metadata or None


def _resolve_canonical_process_value(adapter: dict[str, Any], key: str) -> Any:
    process_mapping = adapter["process"]
    metadata = process_mapping.get("metadata", {})
    candidates = (
        adapter.get(key),
        process_mapping.get(key),
        metadata.get(key),
    )
    return next((value for value in candidates if value is not None), None)


def resolve_source_nodes(adapter: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve adapter source-node container from the authoritative steps list."""
    return adapter["steps"]


def flatten_source_nodes(
    source_nodes: list[Any],
    parent_subprocess: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten nested subprocess nodes into linear node entries."""
    flattened: list[dict[str, Any]] = []
    for a_node in source_nodes:
        node_entry: dict[str, Any] = dict(a_node)
        if parent_subprocess and not node_entry.get("subprocess_parent"):
            node_entry["subprocess_parent"] = parent_subprocess

        nested_nodes = _resolve_subnodes(node_entry)
        flattened.append(node_entry)

        if nested_nodes is not None:
            flattened.extend(
                flatten_source_nodes(nested_nodes, parent_subprocess=node_entry["id"])
            )

    return flattened


def normalize_node_attrs(a_node: dict[str, Any]) -> dict[str, Any]:
    """Normalize node attrs from adapter payload fields and aliases."""
    normalized = dict(a_node.get("attrs", {}))

    for key in (
        "name",
        "lane",
        "location",
        "consumes",
        "produces",
        "performed_by",
        "uses",
        "workers",
        "equipment",
        "note",
        "metadata",
        "inputs",
        "outputs",
        "subprocess_parent",
        "branch",
        "outcomes",
        "routes",
    ):
        if key in a_node:
            normalized.setdefault(key, a_node[key])
    metadata = normalized.get("metadata")
    node_kind = a_node["kind"]
    if metadata is not None:
        normalized_metadata = dict(metadata)
        if (
            node_kind in {"task", "system_task", "subprocess"}
            and "wait_time" in normalized_metadata
            and "wait_before" not in normalized_metadata
        ):
            normalized_metadata["wait_before"] = normalized_metadata.pop("wait_time")
        normalized["metadata"] = normalized_metadata

    # Canonical aliases are populated from legacy keys when explicit canonical
    # values are absent so downstream logic can consume one preferred surface.
    if "consumes" not in normalized and isinstance(normalized.get("inputs"), list):
        normalized["consumes"] = list(normalized["inputs"])
    if "produces" not in normalized and isinstance(normalized.get("outputs"), list):
        normalized["produces"] = list(normalized["outputs"])
    if "performed_by" not in normalized and isinstance(normalized.get("workers"), list):
        normalized["performed_by"] = list(normalized["workers"])
    if "uses" not in normalized and isinstance(normalized.get("equipment"), list):
        normalized["uses"] = list(normalized["equipment"])

    return normalized


def resolve_explicit_transitions(adapter: dict[str, Any]) -> Any:
    """Resolve explicit transitions list from adapter payload."""
    return adapter.get("transitions")


def _is_resource_collection(value: Any) -> bool:
    if isinstance(value, list):
        return True
    if not isinstance(value, dict):
        return False

    has_nested_collection = False
    for group_name, group_value in value.items():
        if not isinstance(group_name, str) or not group_name.strip():
            return False

        if group_name == "name":
            if not isinstance(group_value, str) or not group_value.strip():
                return False
            continue

        if not isinstance(group_value, (list, dict)):
            return False
        has_nested_collection = True

    return has_nested_collection


def _resolve_subnodes(node_entry: dict[str, Any]) -> Any:
    subnodes = node_entry.pop("subnodes", None)
    if subnodes is not None:
        return subnodes
    return node_entry.pop("steps", None) if node_entry["kind"] == "subprocess" else None
