"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

DiagramType = Literal["flowchart", "swimlane"]
RenderProfile = Literal["default", "analysis"]
DetailLevel = Literal["summary", "standard", "verbose"]


@dataclass(frozen=True)
class RenderOptions:
    """Configuration for selecting renderer behavior.

    Defaults preserve current user-facing behavior: DOT flowchart with
    standard detail and default rule profile.
    """

    diagram: DiagramType = "flowchart"
    profile: RenderProfile = "default"
    detail: DetailLevel = "standard"

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "RenderOptions":
        """Create normalized render options from a generic options mapping."""
        if not options:
            return cls()

        diagram_raw = str(options.get("diagram") or "flowchart").strip().lower()
        profile_raw = str(options.get("profile") or "default").strip().lower()
        detail_raw = str(options.get("detail") or "standard").strip().lower()

        diagram: DiagramType = "swimlane" if diagram_raw == "swimlane" else "flowchart"
        profile: RenderProfile = "analysis" if profile_raw == "analysis" else "default"
        if detail_raw == "summary":
            detail: DetailLevel = "summary"
        elif detail_raw == "verbose":
            detail = "verbose"
        else:
            detail = "standard"

        return cls(diagram=diagram, profile=profile, detail=detail)
