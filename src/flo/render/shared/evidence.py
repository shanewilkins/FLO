"""Visible canonical evidence bands for diagrams without publication headers."""

from html import escape
from textwrap import wrap
from typing import Any

from .._process_header import process_evidence_rows
from ..options import RenderOptions


def evidence_lines(
    process: Any, width: float, options: RenderOptions
) -> tuple[str, ...]:
    """Wrap complete evidence text within the diagram's available canvas width."""
    if not options.sppm_show_footer:
        return ()
    columns = max(12, int((width - 48) / 7))
    return tuple(
        line
        for label, value in process_evidence_rows(process)
        for line in wrap(f"{label}: {value}", width=columns)
    )


def evidence_svg(lines: tuple[str, ...], y: float, options: RenderOptions) -> list[str]:
    """Emit supplied evidence text after the diagram without obscuring geometry."""
    theme = options.resolved_theme
    return [
        f'<text data-process-evidence="true" x="24" y="{y + 18 + index * 16:g}" font-family="{theme.svg_font_family}" font-size="12" fill="{theme.role("surface").title_text}">{escape(line)}</text>'
        for index, line in enumerate(lines)
    ]
