"""Shared subprocess detail-map reference helpers.

These helpers define the renderer-safe metadata contract for subprocess
references so non-compiler consumers and compiler validation share one seam.
"""

from __future__ import annotations

from typing import Any

SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS: tuple[str, ...] = (
    "detail_map_ref",
    "detail_map_id",
    "detail_map",
    "detail_map_label",
)


def iter_subprocess_detail_map_reference_values(
    metadata: dict[str, Any],
) -> list[tuple[str, str]]:
    """Return present subprocess detail-map reference fields as normalized strings."""
    values: list[tuple[str, str]] = []
    for key in SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS:
        value = metadata.get(key)
        if isinstance(value, str):
            values.append((key, value.strip()))
        elif value is not None:
            values.append((key, ""))
    return values


def resolve_subprocess_detail_map_reference(
    *, node_id: str, metadata: dict[str, Any]
) -> str:
    """Return the visible detail-map reference label for one subprocess node."""
    for _key, value in iter_subprocess_detail_map_reference_values(metadata):
        if value:
            return value
    return node_id.strip()
