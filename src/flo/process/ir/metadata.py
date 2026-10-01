"""Shared metadata access helpers for IR validation."""

from __future__ import annotations

from typing import Any


def extract_node_metadata(node: Any) -> dict[str, Any]:
    """Return node attrs.metadata when available, else an empty mapping."""
    attrs = getattr(node, "attrs", None)
    if not isinstance(attrs, dict):
        return {}
    metadata = attrs.get("metadata")
    if isinstance(metadata, dict):
        return metadata
    return {}


def extract_process_field(process: Any, field: str) -> Any:
    """Return an explicit canonical or typed-extension process field.

    Dictionary input follows the accepted serialized shape, where the current
    entity collections and render intent remain under ``process.metadata``.
    """
    if not isinstance(process, dict):
        explicit = getattr(process, field, None)
        if explicit is not None:
            return explicit
        metadata = getattr(process, "process_metadata", None)
        serialized_key = "render" if field == "render_intent" else field
        return metadata.get(serialized_key) if isinstance(metadata, dict) else None

    direct = process.get(field)
    if direct is not None:
        return direct
    process_entry = process.get("process")
    if not isinstance(process_entry, dict):
        return None
    nested = process_entry.get(field)
    if nested is not None:
        return nested
    metadata = process_entry.get("metadata")
    if not isinstance(metadata, dict):
        return None
    serialized_key = "render" if field == "render_intent" else field
    return metadata.get(serialized_key)
