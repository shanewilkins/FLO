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

    Dictionary input follows the canonical exchange shape under ``process``.
    """
    serialized_key = "render" if field == "render_intent" else field
    if not isinstance(process, dict):
        return getattr(process, field, None)
    process_entry = process.get("process")
    return (
        process_entry.get(serialized_key) if isinstance(process_entry, dict) else None
    )
