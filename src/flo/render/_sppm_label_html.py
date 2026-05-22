"""HTML label builders for SPPM task nodes."""

from __future__ import annotations

from typing import Any

from ._sppm_node_content import build_sppm_node_content
from ._sppm_task_card import build_sppm_task_card_layout
from ._sppm_themes import SppmNodeStyle
from .options import RenderOptions


def _sppm_html_label(
    node_id: str,
    kind: str,
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    style: SppmNodeStyle,
    note: str,
    options: RenderOptions,
    port_counts: dict[str, int],
) -> str:
    """Build a Graphviz HTML-like table label: colored header + white info sub-row."""
    content = build_sppm_node_content(
        node_id=node_id,
        kind=kind,
        name=name,
        metadata=metadata,
        workers=workers,
        note=note,
        options=options,
    )
    name_text = content.title
    name_html = _html_escape_multiline(name_text, break_tag="<BR/>")
    info_lines = list(content.info_lines)

    body_table = ""
    if info_lines:
        joined = (
            '<BR ALIGN="LEFT"/>'.join(
                _html_escape_multiline(line, break_tag='<BR ALIGN="LEFT"/>')
                for line in info_lines
            )
            + '<BR ALIGN="LEFT"/>'
        )
        body_table = (
            f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" BGCOLOR="white">'
            f'<TR><TD BGCOLOR="white" ALIGN="LEFT">'
            f'<FONT FACE="Helvetica" POINT-SIZE="9">{joined}</FONT>'
            f"</TD></TR></TABLE>"
        )
    card_layout = build_sppm_task_card_layout(content)
    return _wrap_sppm_label_with_ports(
        name_html=name_html,
        body_table=body_table,
        port_counts=port_counts,
        border_color=style.border,
        header_fill=style.fill,
        content_width=card_layout.content_width_px,
    )


def _wrap_sppm_label_with_ports(
    *,
    name_html: str,
    body_table: str,
    port_counts: dict[str, int],
    border_color: str,
    header_fill: str,
    content_width: int,
) -> str:
    """Assemble the full outer HTML table with port columns and header row."""
    in_count = max(0, int(port_counts.get("in", 0)))
    out_count = max(0, int(port_counts.get("out", 0)))
    left_stack = _sppm_port_stack_html(role="in", count=in_count)
    right_stack = _sppm_port_stack_html(role="out", count=out_count)
    table_prefix = (
        f'<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0" '
        f'COLOR="{border_color}" BGCOLOR="white">'
    )
    # Header spans all 3 columns so it fills the full box width.  PORT="boundary_in"
    # is placed here for wrap-layout edges that reference "node":"boundary_in":s.
    header_row = (
        f'<TR><TD COLSPAN="3" BGCOLOR="{header_fill}" ALIGN="CENTER" PORT="boundary_in">'
        f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" BGCOLOR="{header_fill}">'
        f'<TR><TD ALIGN="CENTER"><FONT FACE="Helvetica" POINT-SIZE="11">'
        f"<B>{name_html}</B></FONT></TD></TR>"
        f"</TABLE></TD></TR>"
    )
    hr = "<HR/>" if body_table else ""
    content_col = (
        f'<TD WIDTH="{content_width}">{body_table}</TD>'
        if body_table
        else f'<TD WIDTH="{content_width}"></TD>'
    )
    content_row = (
        f'<TR><TD WIDTH="8">{left_stack}</TD>'
        f"{content_col}"
        f'<TD WIDTH="8">{right_stack}</TD></TR>'
    )
    boundary_row = '<TR><TD></TD><TD PORT="boundary_out" HEIGHT="1"></TD><TD></TD></TR>'
    return f"{table_prefix}{header_row}{hr}{content_row}{boundary_row}</TABLE>>"


def _sppm_port_stack_html(*, role: str, count: int) -> str:
    """Build a narrow port-slot column for attach points on SPPM task nodes."""
    if count <= 0:
        return '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR><TD WIDTH="8" HEIGHT="12"></TD></TR></TABLE>'

    rows = "".join(
        f'<TR><TD PORT="{role}_{slot}" WIDTH="8" HEIGHT="12"></TD></TR>'
        for slot in range(count)
    )
    return f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">{rows}</TABLE>'


def _html_escape(text: str) -> str:
    """Escape special HTML characters for Graphviz HTML-like labels."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_escape_multiline(text: str, break_tag: str) -> str:
    """Escape each line of ``text`` and join with ``break_tag``."""
    return break_tag.join(_html_escape(part) for part in text.split("\n"))
