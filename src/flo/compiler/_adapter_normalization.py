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


def validate_adapter_contract(adapter: dict[str, Any]) -> None:
    """Validate the strict v0.1 adapter contract for compilation.

    Required payload keys are `spec_version`, `process`, and `steps`.
    Compatibility aliases such as `nodes`, `edges`, and `from`/`to`
    transition keys are intentionally rejected.
    """
    _validate_spec_version(adapter)
    _validate_process(adapter)
    _validate_steps(adapter)
    _validate_transitions(adapter)


def _validate_spec_version(adapter: dict[str, Any]) -> None:
    spec_version = adapter.get("spec_version")
    if spec_version != "0.1":
        raise ValueError("spec_version must be present and set to '0.1'")


def _validate_process(adapter: dict[str, Any]) -> None:
    process_raw = adapter.get("process")
    if not isinstance(process_raw, dict):
        raise ValueError("process must be an object")

    process_id = process_raw.get("id")
    process_name = process_raw.get("name")
    if not isinstance(process_id, str) or not process_id.strip():
        raise ValueError("process.id must be a non-empty string")
    if not isinstance(process_name, str) or not process_name.strip():
        raise ValueError("process.name must be a non-empty string")


def _validate_steps(adapter: dict[str, Any]) -> None:
    if "nodes" in adapter:
        raise ValueError("steps is required; nodes alias is not supported")
    steps = adapter.get("steps")
    if not isinstance(steps, list):
        raise ValueError("steps must be a list")


def _validate_transitions(adapter: dict[str, Any]) -> None:
    if "edges" in adapter:
        raise ValueError("transitions must be used; edges alias is not supported")

    transitions = adapter.get("transitions")
    if transitions is None:
        return
    if not isinstance(transitions, list):
        raise ValueError("transitions must be a list when provided")

    for idx, transition in enumerate(transitions):
        _validate_transition_entry(idx=idx, transition=transition)


def _validate_transition_entry(*, idx: int, transition: Any) -> None:
    if not isinstance(transition, dict):
        raise ValueError(f"transitions[{idx}] must be an object")
    if "from" in transition or "to" in transition:
        raise ValueError(f"transitions[{idx}] must use 'source' and 'target' keys")

    source = transition.get("source")
    target = transition.get("target")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"transitions[{idx}].source must be a non-empty string")
    if not isinstance(target, str) or not target.strip():
        raise ValueError(f"transitions[{idx}].target must be a non-empty string")


def resolve_process_name(adapter: dict[str, Any]) -> str:
    """Resolve display/process name from adapter payload."""
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}
    return str(
        process.get("id") or process.get("name") or adapter.get("name") or "unnamed"
    )


def resolve_process_metadata(adapter: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve normalized process metadata payload from adapter model."""
    process_raw = adapter.get("process")
    process: dict[str, Any] = process_raw if isinstance(process_raw, dict) else {}

    metadata_raw = process.get("metadata")
    metadata: dict[str, Any] = (
        dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
    )

    process_id = process.get("id")
    if isinstance(process_id, str) and process_id.strip():
        metadata.setdefault(PROCESS_METADATA_PROCESS_ID_KEY, process_id)

    process_name = process.get("name")
    if isinstance(process_name, str) and process_name.strip():
        metadata.setdefault(PROCESS_METADATA_PROCESS_NAME_KEY, process_name)

    for key in (
        "items",
        "resources",
        "locations",
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


def resolve_source_nodes(adapter: dict[str, Any]) -> Any:
    """Resolve adapter source-node container from the authoritative steps list."""
    return adapter.get("steps")


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
            flattened.extend(
                flatten_source_nodes(nested_nodes, parent_subprocess=next_parent)
            )

    return flattened


def normalize_node_attrs(a_node: dict[str, Any]) -> dict[str, Any]:
    """Normalize node attrs from adapter payload fields and aliases."""
    attrs = a_node.get("attrs")
    normalized: dict[str, Any] = dict(attrs) if isinstance(attrs, dict) else {}

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
    ):
        if key in a_node:
            normalized.setdefault(key, a_node[key])
    outcomes = a_node.get("outcomes")
    if isinstance(outcomes, dict) and "outcomes" not in normalized:
        normalized["outcomes"] = outcomes

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
    if isinstance(subnodes, list):
        return subnodes

    kind = str(node_entry.get("kind") or node_entry.get("type") or "").strip().lower()
    if kind != "subprocess":
        return None

    nested_steps = node_entry.pop("steps", None)
    if isinstance(nested_steps, list):
        return nested_steps

    return None
