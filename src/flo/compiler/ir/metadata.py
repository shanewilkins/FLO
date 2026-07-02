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
