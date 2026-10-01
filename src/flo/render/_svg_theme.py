"""Shared helpers for applying a resolved render theme to SVG output."""

from __future__ import annotations

import json
import re
from html import escape

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


def svg_theme_metadata(options: RenderOptions) -> str:
    """Serialize the resolved theme tokens into deterministic SVG metadata."""
    theme = options.resolved_theme
    payload = {
        "canvas": {"background": theme.canvas_background},
        "name": theme.name,
        "roles": {
            name: {
                "border": role.border,
                "detail_text": role.detail_text,
                "fill": role.fill,
                "title_text": role.title_text,
            }
            for name, role in sorted(theme.roles.items())
        },
        "typography": {
            "font_family": list(theme.font_family),
            "scale": theme.typography_scale,
        },
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        f'<metadata id="flo-theme-tokens" data-flo-theme="{escape(theme.name)}">'
        f"{escape(serialized, quote=False)}</metadata>"
    )


__all__ = ["apply_svg_typography", "svg_theme_metadata"]
