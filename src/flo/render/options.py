"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

DiagramType = Literal["flowchart", "swimlane", "spaghetti", "sppm"]
RenderProfile = Literal["default", "analysis"]
DetailLevel = Literal["summary", "standard", "verbose"]
Orientation = Literal["lr", "tb"]
SubprocessView = Literal["expanded", "parent_only"]
SpaghettiChannel = Literal["both", "material", "people"]
SpaghettiPeopleMode = Literal["aggregate", "worker"]
SppmThemeName = Literal["default", "print", "monochrome"]
LayoutWrap = Literal["auto", "off"]
LayoutFit = Literal["fit-preferred", "fit-strict"]
LayoutSpacing = Literal["standard", "compact"]
SppmStepNumbering = Literal["off", "node", "edge"]
SppmLabelDensity = Literal["full", "compact", "teaching"]
SppmWrapStrategy = Literal["word", "balanced", "hard"]
SppmTruncationPolicy = Literal["ellipsis", "clip", "none"]
SppmOutputProfile = Literal["default", "book", "web", "print", "slide"]

_SPPM_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "book": {
        "orientation": "lr",
        "layout_wrap": "auto",
        "layout_fit": "fit-preferred",
        "layout_max_width_px": 1200,
        "layout_target_columns": 6,
        "sppm_label_density": "compact",
    },
    "web": {
        "orientation": "lr",
        "layout_wrap": "auto",
        "layout_fit": "fit-preferred",
        "layout_max_width_px": 1800,
        "layout_target_columns": 10,
        "sppm_label_density": "full",
    },
    "print": {
        "orientation": "tb",
        "layout_wrap": "auto",
        "layout_fit": "fit-strict",
        "layout_max_width_px": 1000,
        "layout_target_columns": 5,
        "sppm_label_density": "teaching",
    },
    "slide": {
        "orientation": "lr",
        "layout_wrap": "auto",
        "layout_fit": "fit-preferred",
        "layout_max_width_px": 2200,
        "layout_target_columns": 12,
        "sppm_label_density": "compact",
    },
}


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
    sppm_theme: SppmThemeName = "default"
    layout_wrap: LayoutWrap = "off"
    layout_fit: LayoutFit = "fit-preferred"
    layout_spacing: LayoutSpacing = "standard"
    sppm_step_numbering: SppmStepNumbering = "off"
    sppm_label_density: SppmLabelDensity = "full"
    sppm_wrap_strategy: SppmWrapStrategy = "word"
    sppm_truncation_policy: SppmTruncationPolicy = "ellipsis"
    sppm_output_profile: SppmOutputProfile = "default"
    layout_max_width_px: int | None = None
    layout_target_columns: int | None = None
    sppm_max_label_step_name: int | None = None
    sppm_max_label_workers: int | None = None
    sppm_max_label_ctwt: int | None = None

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "RenderOptions":
        """Create normalized render options from a generic options mapping."""
        if not options:
            return cls()

        effective_options = _effective_render_options(options)
        profile = _parse_profile(effective_options)

        return cls(
            diagram=_parse_diagram(effective_options),
            profile=profile,
            detail=_parse_detail(effective_options),
            orientation=_parse_orientation(effective_options),
            show_notes=_parse_bool(effective_options.get("show_notes", False)),
            subprocess_view=_parse_subprocess_view(effective_options),
            spaghetti_channel=_parse_spaghetti_channel(effective_options),
            spaghetti_people_mode=_parse_spaghetti_people_mode(effective_options, profile=profile),
            sppm_theme=_parse_sppm_theme(effective_options),
            layout_wrap=_parse_layout_wrap(effective_options),
            layout_fit=_parse_layout_fit(effective_options),
            layout_spacing=_parse_layout_spacing(effective_options),
            sppm_step_numbering=_parse_sppm_step_numbering(effective_options),
            sppm_label_density=_parse_sppm_label_density(effective_options),
            sppm_wrap_strategy=_parse_sppm_wrap_strategy(effective_options),
            sppm_truncation_policy=_parse_sppm_truncation_policy(effective_options),
            sppm_output_profile=_parse_sppm_output_profile(effective_options),
            layout_max_width_px=_parse_positive_int(effective_options.get("layout_max_width_px")),
            layout_target_columns=_parse_positive_int(effective_options.get("layout_target_columns")),
            sppm_max_label_step_name=_parse_positive_int(effective_options.get("sppm_max_label_step_name")),
            sppm_max_label_workers=_parse_positive_int(effective_options.get("sppm_max_label_workers")),
            sppm_max_label_ctwt=_parse_positive_int(effective_options.get("sppm_max_label_ctwt")),
        )


def _effective_render_options(options: Mapping[str, Any]) -> dict[str, Any]:
    effective = dict(options)
    diagram = _parse_diagram(options)
    if diagram != "sppm":
        return effective

    sppm_profile = _parse_sppm_output_profile(options)
    preset = _SPPM_PROFILE_DEFAULTS.get(sppm_profile)
    if not preset:
        return effective

    for key, value in preset.items():
        effective.setdefault(key, value)
    return effective


def _normalized_option(options: Mapping[str, Any], key: str, default: str) -> str:
    return str(options.get(key) or default).strip().lower()


def _parse_diagram(options: Mapping[str, Any]) -> DiagramType:
    diagram_raw = _normalized_option(options, "diagram", "flowchart")
    if diagram_raw == "swimlane":
        return "swimlane"
    if diagram_raw == "spaghetti":
        return "spaghetti"
    if diagram_raw == "sppm":
        return "sppm"
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


def _parse_sppm_theme(options: Mapping[str, Any]) -> SppmThemeName:
    raw = _normalized_option(options, "sppm_theme", "default")
    if raw in {"print", "print-friendly", "print_friendly"}:
        return "print"
    if raw in {"monochrome", "mono", "greyscale", "grayscale"}:
        return "monochrome"
    return "default"


def _parse_layout_wrap(options: Mapping[str, Any]) -> LayoutWrap:
    raw = _normalized_option(options, "layout_wrap", "off")
    if raw in {"auto", "on", "true", "1"}:
        return "auto"
    return "off"


def _parse_layout_fit(options: Mapping[str, Any]) -> LayoutFit:
    raw = _normalized_option(options, "layout_fit", "fit-preferred")
    if raw in {"fit-strict", "strict"}:
        return "fit-strict"
    return "fit-preferred"


def _parse_layout_spacing(options: Mapping[str, Any]) -> LayoutSpacing:
    raw = _normalized_option(options, "layout_spacing", "standard")
    if raw in {"compact", "tight"}:
        return "compact"
    return "standard"


def _parse_sppm_step_numbering(options: Mapping[str, Any]) -> SppmStepNumbering:
    raw = _normalized_option(options, "sppm_step_numbering", "off")
    if raw in {"node", "nodes"}:
        return "node"
    if raw in {"edge", "edges"}:
        return "edge"
    return "off"


def _parse_sppm_label_density(options: Mapping[str, Any]) -> SppmLabelDensity:
    raw = _normalized_option(options, "sppm_label_density", "full")
    if raw == "compact":
        return "compact"
    if raw in {"teaching", "teach"}:
        return "teaching"
    return "full"


def _parse_sppm_wrap_strategy(options: Mapping[str, Any]) -> SppmWrapStrategy:
    raw = _normalized_option(options, "sppm_wrap_strategy", "word")
    if raw == "balanced":
        return "balanced"
    if raw in {"hard", "char", "character"}:
        return "hard"
    return "word"


def _parse_sppm_truncation_policy(options: Mapping[str, Any]) -> SppmTruncationPolicy:
    raw = _normalized_option(options, "sppm_truncation_policy", "ellipsis")
    if raw in {"clip", "cut"}:
        return "clip"
    if raw in {"none", "off", "disabled"}:
        return "none"
    return "ellipsis"


def _parse_sppm_output_profile(options: Mapping[str, Any]) -> SppmOutputProfile:
    raw = _normalized_option(options, "sppm_output_profile", "default")
    if raw == "book":
        return "book"
    if raw == "web":
        return "web"
    if raw == "print":
        return "print"
    if raw == "slide":
        return "slide"
    return "default"


def _parse_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
