"""Backend-neutral SPPM node appearance helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.process.ir.enums import ProcessValueClass

from ._sppm_metadata_schema import get_metadata_value_class
from ._sppm_themes import SppmNodeStyle
from .options import RenderOptions


@dataclass(frozen=True)
class SppmNodeAppearance:
    """Backend-neutral visual tokens used when rendering an SPPM node."""

    fill: str
    border: str
    title_fill: str = "#0f172a"
    info_fill: str = "#475569"
    stroke_dasharray: str | None = None


def resolve_sppm_value_style(
    *, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeStyle:
    """Resolve task-node value-class styling from the configured SPPM theme."""
    theme = options.resolved_theme
    value_class_raw = get_metadata_value_class(metadata)
    try:
        value_class = ProcessValueClass(value_class_raw) if value_class_raw else None
    except ValueError:
        value_class = None
    role_name = (value_class.value if value_class else "unknown").lower()
    role = theme.role(role_name if role_name in {"va", "rnva", "nva"} else "unknown")
    return SppmNodeStyle(
        fill=role.fill,
        border=role.border,
        title_fill=role.title_text,
        info_fill=role.detail_text,
    )


def resolve_sppm_node_appearance(
    *, kind: str, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeAppearance:
    """Return the backend-neutral appearance for an SPPM node."""
    theme = options.resolved_theme
    normalized_kind = str(kind or "task").lower()

    if normalized_kind in {"start", "end"}:
        return SppmNodeAppearance(
            fill=theme.role("start_end").fill,
            border=theme.role("start_end").border,
        )
    if normalized_kind == "decision":
        return SppmNodeAppearance(
            fill=theme.role("decision").fill,
            border=theme.role("decision").border,
            title_fill=theme.role("decision").title_text,
            info_fill=theme.role("decision").detail_text,
        )
    if normalized_kind == "queue":
        return SppmNodeAppearance(
            fill=theme.role("queue").fill,
            border=theme.role("queue").border,
            title_fill=theme.role("queue").title_text,
            info_fill=theme.role("queue").detail_text,
        )
    if normalized_kind == "subprocess":
        return SppmNodeAppearance(
            fill=theme.role("subprocess").fill,
            border=theme.role("subprocess").border,
            stroke_dasharray="4 4",
        )

    style = resolve_sppm_value_style(metadata=metadata, options=options)
    return SppmNodeAppearance(
        fill=style.fill,
        border=style.border,
        title_fill=style.title_fill,
        info_fill=style.info_fill,
    )
