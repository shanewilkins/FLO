"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import re
from typing import Any, Literal, Mapping, cast

from ._sppm_themes import SppmTheme, parse_custom_sppm_themes

DiagramType = Literal["flowchart", "swimlane", "spaghetti", "sppm"]
RenderProfile = Literal["default", "analysis"]
DetailLevel = Literal["summary", "standard", "verbose"]
Orientation = Literal["lr", "tb"]
SubprocessView = Literal["expanded", "parent_only", "child_map", "inline"]
SppmProjectionMode = Literal["top_level", "child_map", "inline"]
SpaghettiChannel = Literal["both", "material", "people"]
SpaghettiPeopleMode = Literal["aggregate", "worker"]
SppmThemeName = str
LayoutWrap = Literal["auto", "off"]
LayoutFit = Literal["fit-preferred", "fit-strict"]
LayoutSpacing = Literal["standard", "compact"]
SppmStepNumbering = Literal["off", "node", "edge"]
SppmLabelDensity = Literal["full", "compact", "teaching"]
SppmWrapStrategy = Literal["word", "balanced", "hard"]
SppmTruncationPolicy = Literal["ellipsis", "clip", "none"]
SppmOutputProfile = Literal["default", "book", "web", "print", "slide"]
PublicationPageFormatName = Literal["letter", "a4", "legal", "tabloid"]
DimensionUnit = Literal["px", "in", "cm"]
RenderBackend = Literal["svg"]

_DIMENSION_TO_PX: dict[str, float] = {
    "px": 1.0,
    "in": 96.0,
    "cm": 96.0 / 2.54,
}
_DIMENSION_RE = re.compile(
    r"^(?P<value>(?:\d+(?:\.\d+)?|\.\d+))\s*(?P<unit>px|in|cm)?$"
)

_SPPM_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "book": {
        "orientation": "lr",
        "layout_wrap": "auto",
        "layout_fit": "fit-preferred",
        "layout_max_width_px": 1200,
        "layout_target_columns": 6,
        "sppm_label_density": "compact",
        "publication_page_format": "letter",
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
        "publication_page_format": "a4",
    },
    "slide": {
        "orientation": "lr",
        "layout_wrap": "auto",
        "layout_fit": "fit-preferred",
        "layout_max_width_px": 2200,
        "layout_target_columns": 12,
        "sppm_label_density": "compact",
        "publication_page_format": "tabloid",
    },
}


@dataclass(frozen=True)
class Dimension:
    """A positive display dimension that can be normalized to pixels."""

    value: float
    unit: DimensionUnit = "px"

    def to_px(self) -> int:
        """Return the dimension normalized to rounded device pixels."""
        pixels = self.value * _DIMENSION_TO_PX[self.unit]
        return max(1, math.floor(pixels + 0.5))


def parse_dimension(value: Any) -> Dimension | None:
    """Parse a positive dimension in px, in, or cm."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Dimension):
        return value if value.value > 0 else None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return Dimension(value=numeric, unit="px") if numeric > 0 else None
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    if not normalized:
        return None
    match = _DIMENSION_RE.fullmatch(normalized)
    if not match:
        return None

    numeric = float(match.group("value"))
    if numeric <= 0:
        return None

    unit = cast(DimensionUnit, match.group("unit") or "px")
    return Dimension(value=numeric, unit=unit)


@dataclass(frozen=True)
class RenderOptions:
    """Configuration for selecting renderer behavior.

    Defaults render SVG flowcharts with standard detail and default rule profile.
    """

    diagram: DiagramType = "flowchart"
    backend: RenderBackend = "svg"
    profile: RenderProfile = "default"
    detail: DetailLevel = "standard"
    orientation: Orientation = "lr"
    show_notes: bool = False
    subprocess_view: SubprocessView = "expanded"
    sppm_projection: SppmProjectionMode = "top_level"
    sppm_focus_subprocess: str | None = None
    spaghetti_channel: SpaghettiChannel = "both"
    spaghetti_people_mode: SpaghettiPeopleMode = "aggregate"
    sppm_theme: SppmThemeName = "default"
    sppm_themes: dict[str, SppmTheme] = field(default_factory=dict)
    layout_wrap: LayoutWrap = "off"
    layout_fit: LayoutFit = "fit-preferred"
    layout_spacing: LayoutSpacing = "standard"
    sppm_step_numbering: SppmStepNumbering = "off"
    sppm_label_density: SppmLabelDensity = "full"
    sppm_wrap_strategy: SppmWrapStrategy = "word"
    sppm_truncation_policy: SppmTruncationPolicy = "ellipsis"
    sppm_output_profile: SppmOutputProfile = "default"
    sppm_show_header: bool = True
    sppm_show_footer: bool = True
    publication_page_format: PublicationPageFormatName | None = None
    layout_max_width: Dimension | None = None
    layout_max_width_px: int | None = None
    layout_target_columns: int | None = None
    sppm_max_label_step_name: int | None = None
    sppm_max_label_workers: int | None = None
    sppm_max_label_ctwt: int | None = None
    sppm_footer_metrics: tuple[tuple[str, str], ...] = ()
    sppm_footer_notes: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "RenderOptions":
        """Create normalized render options from a generic options mapping."""
        if not options:
            return cls()

        effective_options = _effective_render_options(options)
        profile = _parse_profile(effective_options)
        layout_max_width = _parse_dimension_option(
            "layout_max_width_px",
            effective_options.get("layout_max_width_px"),
        )

        return cls(
            diagram=_parse_diagram(effective_options),
            backend=_parse_backend(effective_options),
            profile=profile,
            detail=_parse_detail(effective_options),
            orientation=_parse_orientation(effective_options),
            show_notes=_parse_bool(effective_options.get("show_notes", False)),
            subprocess_view=_parse_subprocess_view(effective_options),
            sppm_projection=_parse_sppm_projection(effective_options),
            sppm_focus_subprocess=_parse_optional_string(
                effective_options.get("sppm_focus_subprocess")
            ),
            spaghetti_channel=_parse_spaghetti_channel(effective_options),
            spaghetti_people_mode=_parse_spaghetti_people_mode(
                effective_options, profile=profile
            ),
            sppm_theme=_parse_sppm_theme(effective_options),
            sppm_themes=_parse_sppm_themes(effective_options),
            layout_wrap=_parse_layout_wrap(effective_options),
            layout_fit=_parse_layout_fit(effective_options),
            layout_spacing=_parse_layout_spacing(effective_options),
            sppm_step_numbering=_parse_sppm_step_numbering(effective_options),
            sppm_label_density=_parse_sppm_label_density(effective_options),
            sppm_wrap_strategy=_parse_sppm_wrap_strategy(effective_options),
            sppm_truncation_policy=_parse_sppm_truncation_policy(effective_options),
            sppm_output_profile=_parse_sppm_output_profile(effective_options),
            sppm_show_header=not (
                _parse_bool(effective_options.get("no_header", False))
                or _parse_bool(effective_options.get("sppm_no_header", False))
            ),
            sppm_show_footer=not (
                _parse_bool(effective_options.get("no_footer", False))
                or _parse_bool(effective_options.get("sppm_no_footer", False))
            ),
            publication_page_format=_parse_publication_page_format(effective_options),
            layout_max_width=layout_max_width,
            layout_max_width_px=layout_max_width.to_px() if layout_max_width else None,
            layout_target_columns=_parse_positive_int(
                effective_options.get("layout_target_columns")
            ),
            sppm_max_label_step_name=_parse_positive_int(
                effective_options.get("sppm_max_label_step_name")
            ),
            sppm_max_label_workers=_parse_positive_int(
                effective_options.get("sppm_max_label_workers")
            ),
            sppm_max_label_ctwt=_parse_positive_int(
                effective_options.get("sppm_max_label_ctwt")
            ),
            sppm_footer_metrics=_parse_footer_metrics(
                _footer_metric_source(effective_options)
            ),
            sppm_footer_notes=_parse_footer_notes(
                _footer_note_source(effective_options)
            ),
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


def _parse_backend(options: Mapping[str, Any]) -> RenderBackend:
    return "svg"


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
    default = "parent_only" if _parse_diagram(options) == "sppm" else "expanded"
    subprocess_view_raw = _normalized_option(options, "subprocess_view", default)
    if subprocess_view_raw in {
        "parent-only",
        "parent_only",
        "parents-only",
        "parents_only",
    }:
        return "parent_only"
    if subprocess_view_raw in {"child-map", "child_map", "child", "focused-child"}:
        return "child_map"
    if subprocess_view_raw in {"inline", "inline-expand", "inline_expand"}:
        return "inline"
    return "expanded"


def _parse_sppm_projection(options: Mapping[str, Any]) -> SppmProjectionMode:
    raw = _normalized_option(options, "sppm_projection", "")
    if raw in {"child-map", "child_map", "child"}:
        return "child_map"
    if raw in {"inline", "inline-expand", "inline_expand"}:
        return "inline"

    subprocess_view = _parse_subprocess_view(options)
    if subprocess_view == "child_map":
        return "child_map"
    if subprocess_view == "inline":
        return "inline"
    return "top_level"


def _parse_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_spaghetti_channel(options: Mapping[str, Any]) -> SpaghettiChannel:
    raw = _normalized_option(options, "spaghetti_channel", "both")
    if raw in {"material", "materials", "item", "items"}:
        return "material"
    if raw in {"people", "person", "worker", "workers"}:
        return "people"
    return "both"


def _parse_spaghetti_people_mode(
    options: Mapping[str, Any], profile: RenderProfile
) -> SpaghettiPeopleMode:
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
    return raw


def _parse_sppm_themes(options: Mapping[str, Any]) -> dict[str, SppmTheme]:
    return parse_custom_sppm_themes(options.get("sppm_themes"))


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


def _parse_publication_page_format(
    options: Mapping[str, Any],
) -> PublicationPageFormatName | None:
    raw = options.get("publication_page_format")
    if raw is None:
        return None
    normalized = str(raw).strip().lower()
    if normalized == "letter":
        return "letter"
    if normalized == "a4":
        return "a4"
    if normalized == "legal":
        return "legal"
    if normalized == "tabloid":
        return "tabloid"
    raise ValueError(
        "Invalid value for publication_page_format: expected one of letter, a4, legal, or tabloid."
    )


def _parse_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except TypeError, ValueError:
        return None
    return parsed if parsed > 0 else None


def _parse_dimension_option(option_name: str, value: Any) -> Dimension | None:
    if value is None:
        return None
    parsed = parse_dimension(value)
    if parsed is None:
        raise ValueError(
            f"Invalid value for {option_name}: expected a positive dimension using px, in, or cm."
        )
    return parsed


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_footer_metrics(value: Any) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        return ()

    rows: list[tuple[str, str]] = []
    for item in items:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            label, row_value = item
        elif isinstance(item, dict):
            label = item.get("label")
            row_value = item.get("value")
        else:
            continue
        label_text = str(label or "").strip()
        value_text = str(row_value or "").strip()
        if label_text and value_text:
            rows.append((label_text, value_text))
    return tuple(rows)


def _parse_footer_notes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        note = value.strip()
        return (note,) if note else ()
    if not isinstance(value, (list, tuple)):
        return ()
    notes = [str(note).strip() for note in value if str(note).strip()]
    return tuple(notes)


def _footer_metric_source(options: Mapping[str, Any]) -> Any:
    return (
        options.get("sppm_footer_metrics")
        or options.get("sppm_legend_items")
        or options.get("legend_items")
        or options.get("legend")
    )


def _footer_note_source(options: Mapping[str, Any]) -> Any:
    return (
        options.get("sppm_footer_notes")
        or options.get("sppm_caption")
        or options.get("caption")
    )
