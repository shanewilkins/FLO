"""Backend-neutral SPPM node appearance helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.compiler.ir.enums import ProcessValueClass

from ._sppm_metadata_schema import get_metadata_value_class
from ._sppm_themes import SppmNodeStyle, resolve_sppm_theme_with_custom
from .options import RenderOptions


@dataclass(frozen=True)
class SppmNodeAppearance:
    fill: str
    border: str
    title_fill: str = "#0f172a"
    info_fill: str = "#475569"
    stroke_dasharray: str | None = None


def resolve_sppm_value_style(
    *, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeStyle:
    """Resolve task-node value-class styling from the configured SPPM theme."""
    theme = resolve_sppm_theme_with_custom(options.sppm_theme, options.sppm_themes)
    value_class_raw = get_metadata_value_class(metadata)
    try:
        value_class = ProcessValueClass(value_class_raw) if value_class_raw else None
    except ValueError:
        value_class = None
    return theme.style_for(value_class.value if value_class else None)


def resolve_sppm_node_appearance(
    *, kind: str, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeAppearance:
    """Return the backend-neutral appearance for an SPPM node."""
    theme = resolve_sppm_theme_with_custom(options.sppm_theme, options.sppm_themes)
    normalized_kind = str(kind or "task").lower()

    if normalized_kind in {"start", "end"}:
        return SppmNodeAppearance(
            fill=theme.start_end.fill,
            border=theme.start_end.border,
        )
    if normalized_kind == "decision":
        return SppmNodeAppearance(
            fill=theme.decision.fill,
            border=theme.decision.border,
        )
    if normalized_kind == "queue":
        return SppmNodeAppearance(
            fill="#FFB74D",
            border="#E65100",
            info_fill="#7c2d12",
        )
    if normalized_kind == "subprocess":
        return SppmNodeAppearance(
            fill="#F8FAFC",
            border="#607D8B",
            stroke_dasharray="4 4",
        )

    style = resolve_sppm_value_style(metadata=metadata, options=options)
    return SppmNodeAppearance(fill=style.fill, border=style.border)
