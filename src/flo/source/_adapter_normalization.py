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
    validate_source_collections,
    validate_source_shape,
)


def validate_adapter_contract(adapter: dict[str, Any]) -> SourceDocument:
    """Validate source shapes once, then check source-specific relationships."""
    document = validate_source_shape(SourceDocument, adapter)
    validate_source_collections(adapter)
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
    return adapter["process"].get("render")


def resolve_process_lead_time(adapter: dict[str, Any]) -> Any:
    """Return the authored process-level lead-time profile."""
    return adapter["process"].get("lead_time")


def resolve_process_extensions(adapter: dict[str, Any]) -> Any:
    """Return explicit opaque process extensions."""
    return adapter["process"].get("extensions")


def resolve_process_metadata(adapter: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve normalized process metadata payload from adapter model."""
    process = adapter["process"]
    metadata: dict[str, Any] = {}
    metadata.setdefault(PROCESS_METADATA_PROCESS_ID_KEY, process["id"])
    metadata.setdefault(PROCESS_METADATA_PROCESS_NAME_KEY, process["name"])
    return metadata or None


def _resolve_canonical_process_value(adapter: dict[str, Any], key: str) -> Any:
    return adapter["process"].get(key)


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
    """Return control-flow attributes retained by canonical nodes."""
    normalized = dict(a_node.get("attrs", {}))

    for key in (
        "subprocess_parent",
        "branch",
        "outcomes",
        "routes",
    ):
        if key in a_node:
            normalized.setdefault(key, a_node[key])
    return normalized


def resolve_explicit_transitions(adapter: dict[str, Any]) -> Any:
    """Resolve explicit transitions list from adapter payload."""
    return adapter.get("transitions")


def _resolve_subnodes(node_entry: dict[str, Any]) -> Any:
    subnodes = node_entry.pop("subnodes", None)
    if subnodes is not None:
        return subnodes
    return node_entry.pop("steps", None) if node_entry["kind"] == "subprocess" else None
