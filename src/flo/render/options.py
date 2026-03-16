"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

DiagramType = Literal["flowchart", "swimlane"]
RenderProfile = Literal["default", "analysis"]
DetailLevel = Literal["summary", "standard", "verbose"]
Orientation = Literal["lr", "tb"]


@dataclass(frozen=True)
class RenderOptions:
    """Configuration for selecting renderer behavior.

    Defaults preserve current user-facing behavior: DOT flowchart with
    standard detail and default rule profile.
    """

    diagram: DiagramType = "flowchart"
    profile: RenderProfile = "default"
    detail: DetailLevel = "standard"
    orientation: Orientation = "lr"
    show_notes: bool = False

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "RenderOptions":
        """Create normalized render options from a generic options mapping."""
        if not options:
            return cls()

        diagram_raw = str(options.get("diagram") or "flowchart").strip().lower()
        profile_raw = str(options.get("profile") or "default").strip().lower()
        detail_raw = str(options.get("detail") or "standard").strip().lower()
        orientation_raw = str(options.get("orientation") or "lr").strip().lower()
        show_notes_raw = options.get("show_notes", False)

        diagram: DiagramType = "swimlane" if diagram_raw == "swimlane" else "flowchart"
        profile: RenderProfile = "analysis" if profile_raw == "analysis" else "default"
        if detail_raw == "summary":
            detail: DetailLevel = "summary"
        elif detail_raw == "verbose":
            detail = "verbose"
        else:
            detail = "standard"

        if orientation_raw in {"tb", "top-to-bottom", "top_to_bottom", "top to bottom"}:
            orientation: Orientation = "tb"
        else:
            orientation = "lr"

        show_notes = _parse_bool(show_notes_raw)

        return cls(
            diagram=diagram,
            profile=profile,
            detail=detail,
            orientation=orientation,
            show_notes=show_notes,
        )


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
