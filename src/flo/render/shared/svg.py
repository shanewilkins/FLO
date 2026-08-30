"""Renderer-neutral SVG accessibility utilities."""

from __future__ import annotations

from html import escape
from typing import Any

from .._process_header import extract_process_header_context

SVG_ACCESSIBILITY_ATTRIBUTES = (
    'role="img" aria-labelledby="flo-svg-title flo-svg-description"'
)


def svg_accessibility_elements(process: Any, *, diagram_name: str) -> list[str]:
    """Return a deterministic accessible name and description for an SVG."""
    context = extract_process_header_context(process)
    process_title = context.title or "FLO process"
    title = f"{process_title} — {diagram_name}"
    description = (
        f"{diagram_name} diagram for {process_title}. "
        "Read node and transition labels for process details."
    )
    return [
        f'<title id="flo-svg-title">{escape(title)}</title>',
        f'<desc id="flo-svg-description">{escape(description)}</desc>',
    ]
