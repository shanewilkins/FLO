"""Shared helpers for applying a resolved render theme to SVG output."""

from __future__ import annotations

import re

from .options import RenderOptions

_FONT_RE = re.compile(r'font-family="Helvetica"')
_FONT_SIZE_RE = re.compile(r'font-size="(?P<size>\d+(?:\.\d+)?)"')


def apply_svg_typography(content: str, options: RenderOptions) -> str:
    """Apply the resolved family and scale to all renderer-owned SVG text."""
    theme = options.resolved_theme
    content = _FONT_RE.sub(f'font-family="{theme.svg_font_family}"', content)
    if theme.typography_scale == 1.0:
        return content

    def scaled(match: re.Match[str]) -> str:
        return f'font-size="{theme.font_size(float(match.group("size")))}"'

    return _FONT_SIZE_RE.sub(scaled, content)


__all__ = ["apply_svg_typography"]
