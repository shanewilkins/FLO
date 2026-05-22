"""Rework edge metadata label helpers for SPPM routing."""

from __future__ import annotations

import textwrap

from ._callout_layout import (
    build_edge_callout_attrs,
    format_callout_table_html,
    format_callout_text_row,
    resolve_callout_near_source,
)
from ._sppm_rework_content import build_sppm_rework_metadata_lines


def build_sppm_rework_data_box_attrs(
    metadata: object,
    *,
    is_branch_out: bool,
    edge_attrs: tuple[str, ...] = (),
) -> tuple[str, ...] | None:
    """Return compact DOT attrs for a rework data box near the loop origin."""
    lines = list(build_sppm_rework_metadata_lines(metadata))
    if not lines:
        return None

    wrapped_lines: list[str] = []
    for line in lines:
        wrapped = textwrap.wrap(
            line, width=24, break_long_words=False, break_on_hyphens=False
        )
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
    near_source = resolve_callout_near_source(
        prefer_near_source=is_branch_out, edge_attrs=edge_attrs
    )
    return build_edge_callout_attrs(table_html=table_html, near_source=near_source)
