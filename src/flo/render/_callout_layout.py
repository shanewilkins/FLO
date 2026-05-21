"""Shared placement helpers for nearby edge callouts and annotation boxes."""

from __future__ import annotations

from html import escape as html_escape


def build_edge_callout_attrs(
    *,
    table_html: str,
    near_source: bool,
    source_label_distance: str = "0.7",
    source_label_angle: str = "20",
) -> tuple[str, ...]:
    """Return DOT attrs placing a callout near source or along the edge center.

    `near_source=True` places the callout near the edge tail via `taillabel`
    and applies stable distance/angle defaults to avoid crowding nearby nodes.
    `near_source=False` uses `xlabel` for center-ish placement.
    """
    if near_source:
        return (
            f"taillabel=<{table_html}>",
            f'labeldistance="{source_label_distance}"',
            f'labelangle="{source_label_angle}"',
        )
    return (f"xlabel=<{table_html}>",)


def build_edge_text_callout_attrs(
    *,
    text: str,
    near_source: bool,
    source_label_distance: str = "0.7",
    source_label_angle: str = "20",
) -> tuple[str, ...]:
    """Return DOT attrs for a plain-text edge callout label."""
    if near_source:
        return (
            f'taillabel="{text}"',
            f'labeldistance="{source_label_distance}"',
            f'labelangle="{source_label_angle}"',
        )
    return (f'xlabel="{text}"',)


def resolve_callout_near_source(
    *, prefer_near_source: bool, edge_attrs: tuple[str, ...] | list[str]
) -> bool:
    """Return whether a callout should be placed near source to reduce overlap.

    If the edge already has center label attrs (`xlabel=`), prefer source-side
    placement for the callout to avoid callout/label collisions.
    """
    if prefer_near_source:
        return True
    return any(str(attr).startswith("xlabel=") for attr in edge_attrs)


def format_callout_text_row(
    *,
    text: str,
    point_size: str = "10",
    text_color: str = "#455A64",
    bold: bool = False,
    align: str = "LEFT",
    balign: str | None = None,
) -> str:
    """Return one escaped callout table row for Graphviz HTML-like labels."""
    font_open = f'<FONT POINT-SIZE="{point_size}" COLOR="{text_color}">'
    font_close = "</FONT>"
    if bold:
        font_open += "<B>"
        font_close = "</B>" + font_close
    balign_attr = f' BALIGN="{balign}"' if balign is not None else ""
    return (
        f'<TR><TD ALIGN="{align}"{balign_attr}>'
        f"{font_open}{html_escape(text)}{font_close}"
        "</TD></TR>"
    )


def format_callout_table_html(
    *,
    row_html: str,
    border_color: str,
    background_color: str = "#FFFFFF",
    cell_padding: str = "3",
) -> str:
    """Wrap row HTML in a standard callout table envelope."""
    return (
        f'<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="{cell_padding}" '
        f'COLOR="{border_color}" BGCOLOR="{background_color}">'
        f"{row_html}"
        "</TABLE>"
    )
