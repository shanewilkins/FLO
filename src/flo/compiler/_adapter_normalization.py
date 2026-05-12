"""Adapter-facing normalization helpers for compilation.

This module owns adapter payload normalization concerns: process metadata,
source node extraction/flattening, and attribute normalization.
"""

from __future__ import annotations

from typing import Any

from flo.schema.render_metadata import (
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)


def coerce_adapter_model(adapter_model: dict[str, Any] | None) -> dict[str, Any]:
    """Return a dictionary payload for compiler normalization."""
    return adapter_model or {}


def resolve_process_name(adapter: dict[str, Any]) -> str:
    """Resolve display/process name from adapter payload."""
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}
    return str(process.get("id") or process.get("name") or adapter.get("name") or "unnamed")


def resolve_process_metadata(adapter: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve normalized process metadata payload from adapter model."""
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}

    metadata_raw = process.get("metadata")
    metadata: dict[str, Any] = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}

    process_id = process.get("id")
    if isinstance(process_id, str) and process_id.strip():
        metadata.setdefault(PROCESS_METADATA_PROCESS_ID_KEY, process_id)

    process_name = process.get("name")
    if isinstance(process_name, str) and process_name.strip():
        metadata.setdefault(PROCESS_METADATA_PROCESS_NAME_KEY, process_name)

    for key in ("materials", "equipment", "locations", "workers"):
        value = adapter.get(key)
        if not _is_resource_collection(value):
            value = process.get(key)
        if _is_resource_collection(value):
            metadata[key] = value

    return metadata or None


def resolve_source_nodes(adapter: dict[str, Any]) -> Any:
    """Resolve adapter source-node container preserving compatibility aliases."""
    steps = adapter.get("steps")
    if isinstance(steps, list):
        return steps
    return adapter.get("nodes")


def flatten_source_nodes(
    source_nodes: list[Any],
    parent_subprocess: str | None = None,
) -> list[dict[str, Any]]:
    """Flatten nested subprocess nodes into linear node entries."""
    flattened: list[dict[str, Any]] = []
    for a_node in source_nodes:
        if not isinstance(a_node, dict):
            continue

        node_entry: dict[str, Any] = dict(a_node)
        if parent_subprocess and not node_entry.get("subprocess_parent"):
            node_entry["subprocess_parent"] = parent_subprocess

        node_id = node_entry.get("id")
        nested_nodes = _resolve_subnodes(node_entry)
        flattened.append(node_entry)

        if isinstance(nested_nodes, list):
            next_parent = str(node_id) if node_id is not None else None
            flattened.extend(flatten_source_nodes(nested_nodes, parent_subprocess=next_parent))

    return flattened


def normalize_node_attrs(a_node: dict[str, Any]) -> dict[str, Any]:
    """Normalize node attrs from adapter payload fields and aliases."""
    attrs = a_node.get("attrs")
    normalized: dict[str, Any] = dict(attrs) if isinstance(attrs, dict) else {}

    for key in (
        "name",
        "lane",
        "location",
        "workers",
        "equipment",
        "note",
        "metadata",
        "inputs",
        "outputs",
        "subprocess_parent",
    ):
        if key in a_node:
            normalized.setdefault(key, a_node[key])
    outcomes = a_node.get("outcomes")
    if isinstance(outcomes, dict) and "outcomes" not in normalized:
        normalized["outcomes"] = outcomes
    return normalized


def resolve_explicit_transitions(adapter: dict[str, Any]) -> Any:
    """Resolve explicit edge/transitions list from adapter payload."""
    transitions = adapter.get("transitions")
    if isinstance(transitions, list):
        return transitions
    return adapter.get("edges")


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
    if isinstance(subnodes, list):
        return subnodes

    kind = str(node_entry.get("kind") or node_entry.get("type") or "").strip().lower()
    if kind != "subprocess":
        return None

    nested_steps = node_entry.pop("steps", None)
    if isinstance(nested_steps, list):
        return nested_steps

    return None
