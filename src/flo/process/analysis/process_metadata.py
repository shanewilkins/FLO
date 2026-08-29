"""Shared process metadata extraction helpers."""

from __future__ import annotations

from typing import Any


def extract_process_metadata(process: Any) -> dict[str, Any]:
    """Return normalized process-level metadata as a plain dictionary."""
    if hasattr(process, "process_metadata"):
        metadata = getattr(process, "process_metadata", None)
        return metadata if isinstance(metadata, dict) else {}

    if isinstance(process, dict):
        proc = process.get("process")
        if isinstance(proc, dict):
            metadata = proc.get("metadata")
            return metadata if isinstance(metadata, dict) else {}
    return {}
