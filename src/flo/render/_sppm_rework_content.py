"""Backend-neutral rework edge content helpers for SPPM rendering."""

from __future__ import annotations

from typing import Any


def build_sppm_rework_metadata_lines(metadata: object) -> tuple[str, ...]:
    """Return ordered human-readable rework metadata lines for display."""
    if not isinstance(metadata, dict) or not metadata:
        return ()

    ordered_keys = ("rate", "reason", "frequency", "count")
    lines: list[str] = []
    for key in ordered_keys:
        if key not in metadata:
            continue
        formatted = _format_rework_metadata_value(key, metadata.get(key))
        if formatted is not None:
            lines.append(f"{key.replace('_', ' ').title()}: {formatted}")

    if not lines:
        fallback = _format_rework_metadata_value("note", metadata.get("note"))
        if fallback is not None:
            lines.append(f"Note: {fallback}")

    return tuple(lines)


def _format_rework_metadata_value(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        if key in {"rate", "rework_rate"} and 0 <= float(value) <= 1:
            return f"{float(value) * 100:g}%"
        return f"{value:g}" if isinstance(value, float) else str(value)
    text = str(value).strip()
    return text or None
