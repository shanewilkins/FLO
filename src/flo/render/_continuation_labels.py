"""Shared continuation label helpers for wrapped publication output."""

from __future__ import annotations

from collections.abc import Callable

from ._autoformat_wrap import WrapPlan
from ._callout_layout import format_callout_table_html, format_callout_text_row


def build_continuation_label_attrs(
    *,
    source: str,
    target: str,
    wrap_plan: WrapPlan,
    is_secondary: bool,
    reference_formatter: Callable[[str], str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return outgoing and incoming continuation label attrs for a wrapped edge."""
    if not wrap_plan.active or (source, target) not in wrap_plan.boundary_edges:
        return (), ()

    source_chunk = wrap_plan.node_chunk_index.get(source)
    target_chunk = wrap_plan.node_chunk_index.get(target)
    if source_chunk is None or target_chunk is None or source_chunk == target_chunk:
        return (), ()

    source_page = source_chunk + 1
    target_page = target_chunk + 1
    outgoing = format_continuation_html_label(
        text=f"Continue to p{target_page} {reference_formatter(target)}",
        is_secondary=is_secondary,
    )
    incoming = format_continuation_html_label(
        text=f"Continued from p{source_page} {reference_formatter(source)}",
        is_secondary=is_secondary,
    )
    return (f"headlabel=<{outgoing}>",), (f"taillabel=<{incoming}>",)


def format_continuation_html_label(*, text: str, is_secondary: bool) -> str:
    """Return styled HTML-like Graphviz label markup for a continuation."""
    color = "#90A4AE" if is_secondary else "#455A64"
    point_size = "9" if is_secondary else "10"
    row_html = format_callout_text_row(
        text=text,
        point_size=point_size,
        text_color=color,
        bold=not is_secondary,
    )
    return format_callout_table_html(row_html=row_html, border_color=color)
