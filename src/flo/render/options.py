"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

DiagramType = Literal["flowchart", "swimlane", "spaghetti"]
RenderProfile = Literal["default", "analysis"]
DetailLevel = Literal["summary", "standard", "verbose"]
Orientation = Literal["lr", "tb"]
SubprocessView = Literal["expanded", "parent_only"]
SpaghettiChannel = Literal["both", "material", "people"]
SpaghettiPeopleMode = Literal["aggregate", "worker"]


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
    subprocess_view: SubprocessView = "expanded"
    spaghetti_channel: SpaghettiChannel = "both"
    spaghetti_people_mode: SpaghettiPeopleMode = "aggregate"

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "RenderOptions":
        """Create normalized render options from a generic options mapping."""
        if not options:
            return cls()

        profile = _parse_profile(options)

        return cls(
            diagram=_parse_diagram(options),
            profile=profile,
            detail=_parse_detail(options),
            orientation=_parse_orientation(options),
            show_notes=_parse_bool(options.get("show_notes", False)),
            subprocess_view=_parse_subprocess_view(options),
            spaghetti_channel=_parse_spaghetti_channel(options),
            spaghetti_people_mode=_parse_spaghetti_people_mode(options, profile=profile),
        )


def _normalized_option(options: Mapping[str, Any], key: str, default: str) -> str:
    return str(options.get(key) or default).strip().lower()


def _parse_diagram(options: Mapping[str, Any]) -> DiagramType:
    diagram_raw = _normalized_option(options, "diagram", "flowchart")
    if diagram_raw == "swimlane":
        return "swimlane"
    if diagram_raw == "spaghetti":
        return "spaghetti"
    return "flowchart"


def _parse_profile(options: Mapping[str, Any]) -> RenderProfile:
    profile_raw = _normalized_option(options, "profile", "default")
    if profile_raw == "analysis":
        return "analysis"
    return "default"


def _parse_detail(options: Mapping[str, Any]) -> DetailLevel:
    detail_raw = _normalized_option(options, "detail", "standard")
    if detail_raw == "summary":
        return "summary"
    if detail_raw == "verbose":
        return "verbose"
    return "standard"


def _parse_orientation(options: Mapping[str, Any]) -> Orientation:
    orientation_raw = _normalized_option(options, "orientation", "lr")
    if orientation_raw in {"tb", "top-to-bottom", "top_to_bottom", "top to bottom"}:
        return "tb"
    return "lr"


def _parse_subprocess_view(options: Mapping[str, Any]) -> SubprocessView:
    subprocess_view_raw = _normalized_option(options, "subprocess_view", "expanded")
    if subprocess_view_raw in {"parent-only", "parent_only", "parents-only", "parents_only"}:
        return "parent_only"
    return "expanded"


def _parse_spaghetti_channel(options: Mapping[str, Any]) -> SpaghettiChannel:
    raw = _normalized_option(options, "spaghetti_channel", "both")
    if raw in {"material", "materials", "item", "items"}:
        return "material"
    if raw in {"people", "person", "worker", "workers"}:
        return "people"
    return "both"


def _parse_spaghetti_people_mode(options: Mapping[str, Any], profile: RenderProfile) -> SpaghettiPeopleMode:
    raw_value = options.get("spaghetti_people_mode")
    if raw_value is None:
        # Diagnostics/analysis favors per-worker traces by default.
        return "worker" if profile == "analysis" else "aggregate"

    raw = str(raw_value).strip().lower()
    if raw in {"worker", "workers", "per-worker", "per_worker", "trace", "traces"}:
        return "worker"
    return "aggregate"


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
