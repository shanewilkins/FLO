"""Rework edge metadata label helpers for SPPM routing."""

from __future__ import annotations

from html import escape as html_escape
import textwrap


def build_sppm_rework_data_box_attrs(metadata: object, *, is_branch_out: bool) -> tuple[str, ...] | None:
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

    rows = "".join(
        f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="10">{html_escape(line)}</FONT></TD></TR>'
        for line in wrapped_lines
    )
    if is_branch_out:
        label_attr = (
            'taillabel=<'
            '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" '
            'COLOR="#666666" BGCOLOR="#FFFFFF">'
            f"{rows}"
            "</TABLE>>"
        )
        return (label_attr, 'labeldistance="0.7"', 'labelangle="20"')
    label_attr = (
        'xlabel=<'
        '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" '
        'COLOR="#666666" BGCOLOR="#FFFFFF">'
        f"{rows}"
        "</TABLE>>"
    )
    return (label_attr,)


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