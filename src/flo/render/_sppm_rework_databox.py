"""Rework edge metadata label helpers for SPPM routing."""

from __future__ import annotations

import textwrap

from ._callout_layout import (
    build_edge_callout_attrs,
    format_callout_table_html,
    format_callout_text_row,
    resolve_callout_near_source,
)


def build_sppm_rework_data_box_attrs(
    metadata: object,
    *,
    is_branch_out: bool,
    edge_attrs: tuple[str, ...] = (),
) -> tuple[str, ...] | None:
    """Return compact DOT attrs for a rework data box near the loop origin."""
    if not isinstance(metadata, dict) or not metadata:
        return None

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

    if not lines:
        return None

    wrapped_lines: list[str] = []
    for line in lines:
        wrapped = textwrap.wrap(line, width=24, break_long_words=False, break_on_hyphens=False)
        wrapped_lines.extend(wrapped or [line])

    row_html = "".join(
        format_callout_text_row(
            text=line,
            point_size="10",
            text_color="#000000",
            align="LEFT",
            balign="LEFT",
        )
        for line in wrapped_lines
    )
    table_html = format_callout_table_html(
        row_html=row_html,
        border_color="#666666",
        background_color="#FFFFFF",
        cell_padding="3",
    )
    near_source = resolve_callout_near_source(prefer_near_source=is_branch_out, edge_attrs=edge_attrs)
    return build_edge_callout_attrs(table_html=table_html, near_source=near_source)


def _format_rework_metadata_value(key: str, value: object) -> str | None:
    """Format supported rework metadata values for display in the edge data box."""
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