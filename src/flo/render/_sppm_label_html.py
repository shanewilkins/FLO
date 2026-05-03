"""HTML label builders for SPPM task nodes."""

from __future__ import annotations

import textwrap
from typing import Any

from ._sppm_text import apply_density_filter, abbreviate_workers, format_text_field, normalize_space
from ._sppm_themes import SppmNodeStyle
from .options import RenderOptions

_SPPM_TASK_MAX_WIDTH = 220
_SPPM_TASK_MIN_WIDTH = 80
_SPPM_NAME_SOFT_WRAP = 24
_SPPM_DESCRIPTION_SOFT_WRAP = 42
_SPPM_WORKERS_SOFT_WRAP = 36


def _build_label_metric_lines(
    metadata: dict[str, Any],
    workers: list[Any],
    note: str,
    options: RenderOptions,
) -> tuple[str, str, str, str, str]:
    """Return ``(description, ct_line, workers_line, wt_line, notes_line)`` formatted strings."""
    description = _soft_wrap_text(
        normalize_space(str(metadata.get("description") or "")),
        width=_SPPM_DESCRIPTION_SOFT_WRAP,
    )

    ct = metadata.get("cycle_time")
    ct_line = ""
    if isinstance(ct, dict) and ct.get("value") is not None:
        ct_line = format_text_field(
            f"CT: {ct['value']} {ct.get('unit', 'min')}",
            max_len=options.sppm_max_label_ctwt,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )

    workers_line = ""
    if workers:
        workers_text = ", ".join(str(w) for w in workers)
        if options.sppm_label_density == "compact":
            workers_text = abbreviate_workers([str(w) for w in workers])
        if options.sppm_max_label_workers is None:
            workers_line = _soft_wrap_text(f"Workers: {workers_text}", width=_SPPM_WORKERS_SOFT_WRAP)
        else:
            workers_line = format_text_field(
                f"Workers: {workers_text}",
                max_len=options.sppm_max_label_workers,
                wrap_strategy=options.sppm_wrap_strategy,
                truncation_policy=options.sppm_truncation_policy,
                html_break="\n",
            )

    wt = metadata.get("wait_time")
    wt_line = ""
    if isinstance(wt, dict) and wt.get("value") is not None and float(wt["value"]) > 0:
        wt_line = format_text_field(
            f"WT: {wt['value']} {wt.get('unit', 'min')} wait",
            max_len=options.sppm_max_label_ctwt,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )

    notes_line = ""
    if note and getattr(options, "show_notes", False):
        notes_line = f"Note: {normalize_space(note)}"

    return description, ct_line, workers_line, wt_line, notes_line


def _sppm_html_label(
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    style: SppmNodeStyle,
    note: str,
    options: RenderOptions,
    port_counts: dict[str, int],
) -> str:
    """Build a Graphviz HTML-like table label: colored header + white info sub-row."""
    if options.sppm_max_label_step_name is None:
        name_text = _soft_wrap_text(normalize_space(name), width=_SPPM_NAME_SOFT_WRAP)
    else:
        name_text = format_text_field(
            name,
            max_len=options.sppm_max_label_step_name,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )
    name_html = _html_escape_multiline(name_text, break_tag="<BR/>")

    description, ct_line, workers_line, wt_line, notes_line = _build_label_metric_lines(
        metadata, workers, note, options
    )

    info_lines = apply_density_filter(
        density=options.sppm_label_density,
        description=description,
        ct_line=ct_line,
        wt_line=wt_line,
        workers_line=workers_line,
        notes_line=notes_line,
    )

    body_table = ""
    if info_lines:
        joined = "<BR ALIGN=\"LEFT\"/>".join(
            _html_escape_multiline(line, break_tag="<BR ALIGN=\"LEFT\"/>") for line in info_lines
        ) + "<BR ALIGN=\"LEFT\"/>"
        body_table = (
            f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" BGCOLOR="white">'
            f'<TR><TD BGCOLOR="white" ALIGN="LEFT">'
            f'<FONT FACE="Helvetica" POINT-SIZE="9">{joined}</FONT>'
            f'</TD></TR></TABLE>'
        )
    content_width = _estimate_task_node_width(name_text, info_lines)
    return _wrap_sppm_label_with_ports(
        name_html=name_html,
        body_table=body_table,
        port_counts=port_counts,
        border_color=style.border,
        header_fill=style.fill,
        content_width=content_width,
    )


def _estimate_task_node_width(name_text: str, info_lines: list[str]) -> int:
    """Estimate TD width so the box is roughly square; capped at _SPPM_TASK_MAX_WIDTH."""
    name_line_count = name_text.count("\n") + 1
    body_line_count = sum(line.count("\n") + 1 for line in info_lines) if info_lines else 0
    header_pts = name_line_count * 23
    body_pts = body_line_count * 14 + (12 if body_line_count else 0)
    hr_pts = 1 if body_line_count else 0
    estimated_height = header_pts + body_pts + hr_pts
    return max(min(estimated_height, _SPPM_TASK_MAX_WIDTH), _SPPM_TASK_MIN_WIDTH)


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
        f'<B>{name_html}</B></FONT></TD></TR>'
        f'</TABLE></TD></TR>'
    )
    hr = "<HR/>" if body_table else ""
    content_col = (
        f'<TD WIDTH="{content_width}">{body_table}</TD>'
        if body_table
        else f'<TD WIDTH="{content_width}"></TD>'
    )
    content_row = (
        f'<TR><TD WIDTH="8">{left_stack}</TD>'
        f'{content_col}'
        f'<TD WIDTH="8">{right_stack}</TD></TR>'
    )
    boundary_row = '<TR><TD></TD><TD PORT="boundary_out" HEIGHT="1"></TD><TD></TD></TR>'
    return f'{table_prefix}{header_row}{hr}{content_row}{boundary_row}</TABLE>>'


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


def _soft_wrap_text(text: str, *, width: int) -> str:
    """Wrap ``text`` at ``width`` characters without breaking words."""
    if not text or width < 2:
        return text
    wrapped = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    return "\n".join(wrapped) if wrapped else text
