"""Render option types for diagram projections and detail controls."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, field, fields
from typing import Annotated, Any, Literal, cast, get_args, get_origin, get_type_hints

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    create_model,
    model_validator,
)

from ._publication import resolve_publication_page_format
from .legacy_sppm_themes import SppmTheme, parse_custom_sppm_themes
from .themes import DEFAULT_THEME, RenderTheme, resolve_render_theme

DiagramType = Literal["swimlane", "spaghetti", "sppm", "value_stream"]
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
LayoutOverflow = Literal["safe-fit", "error", "expand", "scale", "paginate"]
SppmStepNumbering = Literal["off", "node", "edge"]
SppmLabelDensity = Literal["full", "compact", "teaching"]
SppmWrapStrategy = Literal["word", "balanced", "hard"]
SppmTruncationPolicy = Literal["ellipsis", "clip", "none"]
SppmOutputProfile = Literal["default", "book", "web", "print", "slide"]
PublicationPageFormatName = Literal["letter", "a4", "legal", "tabloid"]
DimensionUnit = Literal["px", "in", "cm", "mm"]
RenderBackend = Literal["svg"]

_DIMENSION_TO_PX: dict[str, float] = {
    "px": 1.0,
    "in": 96.0,
    "cm": 96.0 / 2.54,
    "mm": 96.0 / 25.4,
}
_DIMENSION_RE = re.compile(
    r"^(?P<value>(?:\d+(?:\.\d+)?|\.\d+))\s*(?P<unit>px|in|cm|mm)?$"
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
        "theme": "print",
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
    """Parse a positive dimension in px, in, cm, or mm."""
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

    Defaults render SVG SPPM with standard detail and safe geometry fitting.
    """

    diagram: DiagramType = "sppm"
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
    spaghetti_strict_spatial: bool = False
    sppm_theme: SppmThemeName = "default"
    sppm_themes: dict[str, SppmTheme] = field(default_factory=dict)
    theme: str | None = None
    themes: dict[str, Any] = field(default_factory=dict)
    background_color: str | None = None
    font_family: tuple[str, ...] | str | None = None
    typography_scale: float | None = None
    resolved_theme: RenderTheme = field(default=DEFAULT_THEME, init=False)
    layout_wrap: LayoutWrap = "off"
    layout_fit: LayoutFit = "fit-preferred"
    layout_spacing: LayoutSpacing = "standard"
    layout_overflow: LayoutOverflow = "safe-fit"
    sppm_step_numbering: SppmStepNumbering = "off"
    sppm_label_density: SppmLabelDensity = "full"
    sppm_wrap_strategy: SppmWrapStrategy = "word"
    sppm_truncation_policy: SppmTruncationPolicy = "ellipsis"
    sppm_output_profile: SppmOutputProfile = "default"
    sppm_show_header: bool = True
    sppm_show_footer: bool = True
    publication_page_format: PublicationPageFormatName | None = None
    layout_width: Dimension | None = None
    layout_height: Dimension | None = None
    layout_width_px: int | None = None
    layout_height_px: int | None = None
    layout_max_width: Dimension | None = None
    layout_max_width_px: int | None = None
    layout_target_columns: int | None = None
    sppm_max_label_step_name: int | None = None
    sppm_max_label_workers: int | None = None
    sppm_max_label_ctwt: int | None = None
    sppm_footer_metrics: tuple[tuple[str, str], ...] = ()
    sppm_footer_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Resolve the single immutable theme consumed by every renderer."""
        object.__setattr__(
            self,
            "resolved_theme",
            resolve_render_theme(
                selected_name=self.theme or self.sppm_theme,
                definitions=self.themes,
                legacy_sppm_themes=self.sppm_themes,
                background_color=self.background_color,
                font_family=self.font_family,
                typography_scale=self.typography_scale,
                strict_name=self.theme is not None,
            ),
        )

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> RenderOptions:
        """Validate and normalize mappings through the shared Pydantic input model."""
        if not options:
            return cls()
        parsed = RenderInput.model_validate(dict(options))
        values = {name: getattr(parsed, name) for name in RenderInput.model_fields}
        maximum = values.pop("layout_max_width_px")
        return cls(
            **values,
            layout_width_px=values["layout_width"].to_px()
            if values["layout_width"]
            else None,
            layout_height_px=values["layout_height"].to_px()
            if values["layout_height"]
            else None,
            layout_max_width=maximum,
            layout_max_width_px=maximum.to_px() if maximum else None,
        )


def _parse_optional_string(value: Any) -> Any:
    return value.strip() or None if isinstance(value, str) else value


def _parse_theme_definitions(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return {} if value is None else value
    return {str(name).strip(): raw for name, raw in value.items() if str(name).strip()}


def _parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    try:
        return float(value)
    except TypeError, ValueError:
        # Preserve the invalid value for the central validator's diagnostic.
        return cast(Any, value)


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


POSITIVE_INTEGER_OPTIONS = frozenset(
    {
        "layout_target_columns",
        "sppm_max_label_step_name",
        "sppm_max_label_workers",
        "sppm_max_label_ctwt",
    }
)
_DIMENSION_OPTIONS = frozenset({"layout_width", "layout_height", "layout_max_width_px"})
_OPTION_ALIASES = {
    "orientation": {
        "top-to-bottom": "tb",
        "top_to_bottom": "tb",
        "top to bottom": "tb",
    },
    "subprocess_view": {
        "parent-only": "parent_only",
        "parents-only": "parent_only",
        "parents_only": "parent_only",
        "child-map": "child_map",
        "child": "child_map",
        "focused-child": "child_map",
        "inline-expand": "inline",
        "inline_expand": "inline",
    },
    "sppm_projection": {
        "child-map": "child_map",
        "child": "child_map",
        "inline-expand": "inline",
        "inline_expand": "inline",
    },
    "spaghetti_channel": {
        "materials": "material",
        "item": "material",
        "items": "material",
        "person": "people",
        "worker": "people",
        "workers": "people",
    },
    "spaghetti_people_mode": {
        "workers": "worker",
        "per-worker": "worker",
        "per_worker": "worker",
        "trace": "worker",
        "traces": "worker",
    },
    "layout_wrap": {"on": "auto", "true": "auto", "1": "auto"},
    "layout_fit": {"strict": "fit-strict"},
    "layout_spacing": {"tight": "compact"},
    "sppm_step_numbering": {"nodes": "node", "edges": "edge"},
    "sppm_label_density": {"teach": "teaching"},
    "sppm_wrap_strategy": {"char": "hard", "character": "hard"},
    "sppm_truncation_policy": {"cut": "clip", "off": "none", "disabled": "none"},
    "sppm_theme": {
        "print-friendly": "print",
        "print_friendly": "print",
        "mono": "monochrome",
        "greyscale": "monochrome",
        "grayscale": "monochrome",
    },
}
_OPTION_FIELDS = {item.name: item for item in fields(RenderOptions) if item.init}
_OPTION_TYPES = get_type_hints(RenderOptions)
_CHOICE_FIELDS = {
    name for name in _OPTION_FIELDS if get_origin(_OPTION_TYPES[name]) is Literal
}


def _choice(name: str, value: Any) -> Any:
    if value is not None and not isinstance(value, str) and name != "layout_wrap":
        return value
    if name == "layout_wrap" and isinstance(value, float):
        return value
    default = cast(str, _OPTION_FIELDS[name].default)
    normalized = str(value or default).strip().lower()
    normalized = _OPTION_ALIASES.get(name, {}).get(normalized, normalized)
    return normalized if normalized in get_args(_OPTION_TYPES[name]) else default


def _positive_integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("expected a positive integer")
    try:
        parsed = int(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError("expected a positive integer") from exc
    if parsed <= 0 or (isinstance(value, float) and value != parsed):
        raise ValueError("expected a positive integer")
    return parsed


def _dimension(value: Any) -> Dimension:
    parsed = parse_dimension(value)
    if parsed is None or not math.isfinite(parsed.value):
        raise ValueError(
            "expected a positive dimension using px, in, cm, or mm (finite)"
        )
    return parsed


def _page_format(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    resolve_publication_page_format(normalized)
    return normalized


def _font_family(value: Any) -> Any:
    return tuple(value) if isinstance(value, list) else value


class _RenderInputRules(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases_and_profiles(cls, value: Any) -> Any:
        """Apply existing alias/default policy before typed field validation."""
        if not isinstance(value, Mapping):
            return value
        raw = dict(value)
        raw["diagram"] = _choice("diagram", raw.get("diagram"))
        profile = _choice("sppm_output_profile", raw.get("sppm_output_profile"))
        if raw["diagram"] == "sppm" and isinstance(profile, str):
            raw = {**_SPPM_PROFILE_DEFAULTS.get(profile, {}), **raw}
        choices = {name: _choice(name, raw.get(name)) for name in _CHOICE_FIELDS}
        choices["backend"] = "svg"
        view_default = "parent_only" if choices["diagram"] == "sppm" else "expanded"
        view = raw.get("subprocess_view")
        choices["subprocess_view"] = _choice(
            "subprocess_view", view_default if view is None or view == "" else view
        )
        projection = _choice("sppm_projection", raw.get("sppm_projection"))
        choices["sppm_projection"] = (
            projection
            if projection != "top_level"
            else choices["subprocess_view"]
            if choices["subprocess_view"] in ("child_map", "inline")
            else "top_level"
        )
        if raw.get("spaghetti_people_mode") is None:
            choices["spaghetti_people_mode"] = (
                "worker" if choices["profile"] == "analysis" else "aggregate"
            )
        theme = str(raw.get("sppm_theme") or "default").strip().lower()
        raw["sppm_theme"] = _OPTION_ALIASES["sppm_theme"].get(theme, theme)
        return {**raw, **choices, **_footer_options(raw)}


def _first_option(raw: Mapping, names: tuple[str, ...]) -> Any:
    return next((raw[name] for name in names if raw.get(name)), None)


def _footer_options(raw: Mapping) -> dict:
    return {
        **{
            f"sppm_show_{suffix}": not any(
                _parse_bool(raw.get(key, False))
                for key in (f"no_{suffix}", f"sppm_no_{suffix}")
            )
            for suffix in ("header", "footer")
        },
        "sppm_footer_metrics": _first_option(
            raw, ("sppm_footer_metrics", "sppm_legend_items", "legend_items", "legend")
        ),
        "sppm_footer_notes": _first_option(
            raw, ("sppm_footer_notes", "sppm_caption", "caption")
        ),
    }


def _input_field(name: str, definition: Any) -> Any:
    annotation = _OPTION_TYPES[name]
    handler = {
        "sppm_themes": parse_custom_sppm_themes,
        "themes": _parse_theme_definitions,
        "font_family": _font_family,
        "typography_scale": _parse_optional_float,
        "publication_page_format": _page_format,
        "sppm_footer_metrics": _parse_footer_metrics,
        "sppm_footer_notes": _parse_footer_notes,
    }.get(name)
    if name == "themes":
        annotation = dict[str, dict[str, Any]]
    if name in POSITIVE_INTEGER_OPTIONS:
        handler = _positive_integer
    elif name in _DIMENSION_OPTIONS:
        annotation, handler = Dimension | None, _dimension
    elif annotation is bool:
        handler = _parse_bool
    elif name in {"sppm_focus_subprocess", "theme", "background_color"}:
        handler = _parse_optional_string
    if handler is not None:
        annotation = Annotated[annotation, BeforeValidator(handler)]
    default = (
        Field(default_factory=definition.default_factory)
        if definition.default_factory is not MISSING
        else definition.default
    )
    return annotation, default


# The dataclass owns fields, types and defaults; the input model adds boundary rules.
RenderInput = create_model(
    "RenderInput",
    __base__=_RenderInputRules,
    **{
        name: _input_field(name, definition)
        for name, definition in _OPTION_FIELDS.items()
        if name not in {"layout_width_px", "layout_height_px", "layout_max_width"}
    },
)
