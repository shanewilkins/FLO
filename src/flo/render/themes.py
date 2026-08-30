"""Central typed theme registry and deterministic theme resolution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from html import escape
import re
from types import MappingProxyType
from typing import Any, Mapping

_COLOR_RE = re.compile(r"^(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8})$")
_NAMED_COLORS = {"black", "white", "transparent"}
_MIN_TYPOGRAPHY_SCALE = 0.75
_MAX_TYPOGRAPHY_SCALE = 1.50

ROLE_NAMES = (
    "va",
    "rnva",
    "nva",
    "unknown",
    "decision",
    "queue",
    "start_end",
    "subprocess",
    "surface",
    "lane",
    "connector",
    "publication",
    "annotation",
    "callout",
    "token",
    "boundary",
    "material_route",
    "information_route",
    "people_route",
    "location_storage",
    "location_transit",
    "location_processing",
    "location_staging",
    "location_support",
    "location_unknown",
)


class ThemeValidationError(ValueError):
    """Raised when a shared theme definition cannot be resolved safely."""


@dataclass(frozen=True)
class ThemeRole:
    """Colors for one shared semantic presentation role."""

    fill: str
    border: str
    title_text: str = "#0f172a"
    detail_text: str = "#475569"


@dataclass(frozen=True)
class RenderTheme:
    """Immutable renderer-neutral theme consumed by maintained renderers."""

    name: str
    canvas_background: str
    font_family: tuple[str, ...]
    typography_scale: float
    roles: Mapping[str, ThemeRole]

    def role(self, name: str) -> ThemeRole:
        """Return a registered semantic role."""
        return self.roles[name]

    @property
    def svg_font_family(self) -> str:
        """Return the ordered font fallback list escaped for an SVG attribute."""
        return escape(", ".join(self.font_family), quote=True)

    def font_size(self, base_px: float) -> str:
        """Return a stable SVG font-size token after applying the theme scale."""
        value = base_px * self.typography_scale
        if abs(value - round(value)) < 0.000_001:
            return str(int(round(value)))
        return f"{value:.2f}".rstrip("0").rstrip(".")


def _roles(**overrides: ThemeRole) -> Mapping[str, ThemeRole]:
    base = {
        "va": ThemeRole("#81C784", "#2E7D32"),
        "rnva": ThemeRole("#FFF176", "#F9A825"),
        "nva": ThemeRole("#EF9A9A", "#C62828"),
        "unknown": ThemeRole("#FFFFFF", "#9E9E9E"),
        "decision": ThemeRole("#E3EEF7", "#285B8F"),
        "queue": ThemeRole("#FFB74D", "#E65100"),
        "start_end": ThemeRole("#FFFFFF", "#333333"),
        "subprocess": ThemeRole("#F8FAFC", "#607D8B"),
        "surface": ThemeRole("#FFFFFF", "#cbd5e1", "#0f172a", "#475569"),
        "lane": ThemeRole("#f8fafc", "#cbd5e1", "#334155", "#475569"),
        "connector": ThemeRole("#FFFFFF", "#475569", "#0f172a", "#475569"),
        "publication": ThemeRole("#fffdf8", "#cbd5e1", "#0f172a", "#334155"),
        "annotation": ThemeRole("#fffdf8", "#666666", "#0f172a", "#475569"),
        "callout": ThemeRole("#ffffff", "#666666", "#0f172a", "#475569"),
        "token": ThemeRole("#ffffff", "#455A64", "#455A64", "#455A64"),
        "boundary": ThemeRole("#FFFFFF", "gray", "gray", "gray"),
        "material_route": ThemeRole("#FFFFFF", "tomato", "tomato", "tomato"),
        "information_route": ThemeRole(
            "#FFFFFF", "royalblue", "royalblue", "royalblue"
        ),
        "people_route": ThemeRole("#FFFFFF", "royalblue", "royalblue", "royalblue"),
        "location_storage": ThemeRole("lemonchiffon", "goldenrod"),
        "location_transit": ThemeRole("mintcream", "slategray"),
        "location_processing": ThemeRole("mistyrose", "firebrick"),
        "location_staging": ThemeRole("honeydew", "seagreen"),
        "location_support": ThemeRole("azure", "deepskyblue"),
        "location_unknown": ThemeRole("aliceblue", "steelblue"),
    }
    base.update(overrides)
    return MappingProxyType(base)


DEFAULT_THEME = RenderTheme(
    name="default",
    canvas_background="#fffdf8",
    font_family=("Helvetica",),
    typography_scale=1.0,
    roles=_roles(),
)


def _with_roles(theme: RenderTheme, name: str, **roles: ThemeRole) -> RenderTheme:
    merged = dict(theme.roles)
    merged.update(roles)
    return replace(theme, name=name, roles=MappingProxyType(merged))


BUILTIN_THEMES: Mapping[str, RenderTheme] = MappingProxyType(
    {
        "default": DEFAULT_THEME,
        "flatly": _with_roles(
            DEFAULT_THEME,
            "flatly",
            va=ThemeRole("#D1F2EB", "#18BC9C", "#0A4B3E"),
            rnva=ThemeRole("#FDEBD0", "#F39C12", "#613E07"),
            nva=ThemeRole("#FADBD8", "#E74C3C", "#5C1E18"),
            decision=ThemeRole("#D5D8DC", "#2C3E50", "#121920"),
            queue=ThemeRole("#F39C12", "#C27D0E", "#2C3E50"),
            unknown=ThemeRole("#FFFFFF", "#95A5A6", "#2C3E50"),
            start_end=ThemeRole("#FFFFFF", "#2C3E50", "#2C3E50"),
        ),
        "print": _with_roles(
            replace(DEFAULT_THEME, name="print", canvas_background="#FFFFFF"),
            "print",
            va=ThemeRole("#D5E8D4", "#1A5C1A"),
            rnva=ThemeRole("#DAE8FC", "#23527C"),
            nva=ThemeRole("#F8CECC", "#8B0000"),
            decision=ThemeRole("#FFFFFF", "#000000"),
            queue=ThemeRole("#FFFFFF", "#000000"),
            unknown=ThemeRole("#FFFFFF", "#555555"),
            start_end=ThemeRole("#FFFFFF", "#000000"),
        ),
        "monochrome": _with_roles(
            replace(DEFAULT_THEME, name="monochrome", canvas_background="#FFFFFF"),
            "monochrome",
            va=ThemeRole("#CCCCCC", "#333333"),
            rnva=ThemeRole("#888888", "#333333"),
            nva=ThemeRole("#444444", "#000000", "#FFFFFF", "#FFFFFF"),
            decision=ThemeRole("#FFFFFF", "#333333"),
            queue=ThemeRole("#777777", "#000000", "#000000", "#000000"),
            unknown=ThemeRole("#FFFFFF", "#333333"),
            start_end=ThemeRole("#FFFFFF", "#333333"),
        ),
    }
)


def resolve_render_theme(
    *,
    selected_name: str | None,
    definitions: Any = None,
    legacy_sppm_themes: Mapping[str, Any] | None = None,
    background_color: Any = None,
    font_family: Any = None,
    typography_scale: Any = None,
    strict_name: bool = True,
) -> RenderTheme:
    """Resolve inheritance, legacy adapters, and direct property overrides."""
    raw_definitions = definitions if isinstance(definitions, Mapping) else {}
    cache: dict[str, RenderTheme] = dict(BUILTIN_THEMES)
    legacy = legacy_sppm_themes or {}
    resolving: list[str] = []

    def resolve(name: str) -> RenderTheme:
        if name in raw_definitions:
            if name in resolving:
                cycle = " -> ".join((*resolving, name))
                raise ThemeValidationError(f"Theme inheritance cycle: {cycle}.")
            raw = raw_definitions[name]
            if not isinstance(raw, Mapping):
                raise ThemeValidationError(f"themes.{name} must be a table.")
            resolving.append(name)
            parent_name = str(
                raw.get("extends") or (name if name in BUILTIN_THEMES else "default")
            ).strip()
            if parent_name == name:
                parent = BUILTIN_THEMES.get(name)
                if parent is None:
                    raise ThemeValidationError(f"Theme '{name}' cannot extend itself.")
            else:
                if (
                    parent_name not in raw_definitions
                    and parent_name not in BUILTIN_THEMES
                    and parent_name not in legacy
                ):
                    raise ThemeValidationError(
                        f"themes.{name}.extends references unknown theme '{parent_name}'."
                    )
                parent = resolve(parent_name)
            resolved = _apply_definition(parent, name=name, raw=raw)
            resolving.pop()
            cache[name] = resolved
            return resolved
        if name in cache:
            return cache[name]
        if name in legacy:
            adapted = _adapt_legacy_sppm_theme(name, legacy[name])
            cache[name] = adapted
            return adapted
        raise ThemeValidationError(f"Unknown render theme '{name}'.")

    # Validate the complete configured registry deterministically, not only the
    # selected inheritance chain, so broken reusable themes cannot hide.
    for configured_name in sorted(str(name) for name in raw_definitions):
        resolve(configured_name)

    normalized_name = _theme_alias(selected_name or "default")
    try:
        theme = resolve(normalized_name)
    except ThemeValidationError:
        if strict_name:
            raise
        theme = DEFAULT_THEME

    if background_color is not None:
        theme = replace(
            theme,
            canvas_background=_parse_color(background_color, "background_color"),
        )
    if font_family is not None:
        theme = replace(
            theme, font_family=_parse_font_family(font_family, "font_family")
        )
    if typography_scale is not None:
        theme = replace(
            theme,
            typography_scale=_parse_scale(typography_scale, "typography_scale"),
        )
    return theme


def _apply_definition(
    parent: RenderTheme, *, name: str, raw: Mapping[str, Any]
) -> RenderTheme:
    unknown = set(raw) - {"extends", "canvas", "typography", "roles"}
    if unknown:
        item = sorted(unknown)[0]
        raise ThemeValidationError(
            f"themes.{name}.{item} is not a registered theme field."
        )
    canvas_background = _resolve_canvas_background(
        parent.canvas_background,
        name=name,
        canvas=raw.get("canvas"),
    )
    font_family, scale = _resolve_typography(
        parent.font_family,
        parent.typography_scale,
        name=name,
        typography=raw.get("typography"),
    )
    roles = _resolve_theme_roles(parent.roles, name=name, raw_roles=raw.get("roles"))
    return RenderTheme(
        name=name,
        canvas_background=canvas_background,
        font_family=font_family,
        typography_scale=scale,
        roles=MappingProxyType(roles),
    )


def _resolve_canvas_background(inherited: str, *, name: str, canvas: Any) -> str:
    if canvas is not None:
        if not isinstance(canvas, Mapping):
            raise ThemeValidationError(f"themes.{name}.canvas must be a table.")
        extra = set(canvas) - {"background"}
        if extra:
            raise ThemeValidationError(
                f"themes.{name}.canvas.{sorted(extra)[0]} is not supported."
            )
        if "background" in canvas:
            return _parse_color(
                canvas["background"], f"themes.{name}.canvas.background"
            )
    return inherited


def _resolve_typography(
    inherited_family: tuple[str, ...],
    inherited_scale: float,
    *,
    name: str,
    typography: Any,
) -> tuple[tuple[str, ...], float]:
    font_family = inherited_family
    scale = inherited_scale
    if typography is not None:
        if not isinstance(typography, Mapping):
            raise ThemeValidationError(f"themes.{name}.typography must be a table.")
        extra = set(typography) - {"font_family", "scale"}
        if extra:
            raise ThemeValidationError(
                f"themes.{name}.typography.{sorted(extra)[0]} is not supported."
            )
        if "font_family" in typography:
            font_family = _parse_font_family(
                typography["font_family"], f"themes.{name}.typography.font_family"
            )
        if "scale" in typography:
            scale = _parse_scale(typography["scale"], f"themes.{name}.typography.scale")
    return font_family, scale


def _resolve_theme_roles(
    inherited: Mapping[str, ThemeRole], *, name: str, raw_roles: Any
) -> dict[str, ThemeRole]:
    roles = dict(inherited)
    if raw_roles is not None:
        if not isinstance(raw_roles, Mapping):
            raise ThemeValidationError(f"themes.{name}.roles must be a table.")
        for role_name, role_raw in raw_roles.items():
            role_name = str(role_name).strip()
            if role_name not in ROLE_NAMES:
                raise ThemeValidationError(
                    f"themes.{name}.roles.{role_name} is not a registered role."
                )
            if not isinstance(role_raw, Mapping):
                raise ThemeValidationError(
                    f"themes.{name}.roles.{role_name} must be a table."
                )
            roles[role_name] = _apply_role(
                roles[role_name], role_raw, f"themes.{name}.roles.{role_name}"
            )
    return roles


def _apply_role(parent: ThemeRole, raw: Mapping[str, Any], path: str) -> ThemeRole:
    aliases = {"title_fill": "title_text", "info_fill": "detail_text"}
    normalized = {aliases.get(str(key), str(key)): value for key, value in raw.items()}
    unknown = set(normalized) - {"fill", "border", "title_text", "detail_text"}
    if unknown:
        raise ThemeValidationError(f"{path}.{sorted(unknown)[0]} is not supported.")
    values = {
        field: _parse_color(normalized[field], f"{path}.{field}")
        if field in normalized
        else getattr(parent, field)
        for field in ("fill", "border", "title_text", "detail_text")
    }
    return ThemeRole(**values)


def _parse_color(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ThemeValidationError(f"{path} must be a non-empty CSS color.")
    color = value.strip()
    if not _COLOR_RE.fullmatch(color) and color.lower() not in _NAMED_COLORS:
        raise ThemeValidationError(
            f"{path} must use #RGB, #RRGGBB, #RRGGBBAA, black, white, or transparent."
        )
    return color


def _parse_font_family(value: Any, path: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        raise ThemeValidationError(
            f"{path} must be a non-empty string or list of strings."
        )
    families = tuple(str(item).strip() for item in values if str(item).strip())
    if not families:
        raise ThemeValidationError(f"{path} must contain at least one font family.")
    return families


def _parse_scale(value: Any, path: str) -> float:
    if isinstance(value, bool):
        raise ThemeValidationError(f"{path} must be a number from 0.75 through 1.5.")
    try:
        scale = float(value)
    except (TypeError, ValueError) as exc:
        raise ThemeValidationError(
            f"{path} must be a number from 0.75 through 1.5."
        ) from exc
    if not _MIN_TYPOGRAPHY_SCALE <= scale <= _MAX_TYPOGRAPHY_SCALE:
        raise ThemeValidationError(f"{path} must be from 0.75 through 1.5.")
    return scale


def _adapt_legacy_sppm_theme(name: str, legacy: Any) -> RenderTheme:
    roles = dict(DEFAULT_THEME.roles)
    for role_name in ("va", "rnva", "nva", "unknown", "decision", "queue", "start_end"):
        style = getattr(legacy, role_name)
        roles[role_name] = ThemeRole(
            fill=style.fill,
            border=style.border,
            title_text=style.title_fill,
            detail_text=style.info_fill,
        )
    return replace(DEFAULT_THEME, name=name, roles=MappingProxyType(roles))


def _theme_alias(name: str) -> str:
    raw = str(name).strip()
    normalized = raw.lower()
    if normalized in {"print-friendly", "print_friendly"}:
        return "print"
    if normalized in {"mono", "greyscale", "grayscale"}:
        return "monochrome"
    if normalized in BUILTIN_THEMES:
        return normalized
    return raw or "default"


def contrast_ratio(foreground: str, background: str) -> float | None:
    """Return WCAG contrast for six-digit hex colors, or None if unsupported."""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", foreground) or not re.fullmatch(
        r"#[0-9a-fA-F]{6}", background
    ):
        return None

    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2])

    foreground_luminance = luminance(foreground)
    background_luminance = luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def theme_contrast_risks(
    theme: RenderTheme, *, minimum_ratio: float = 4.5
) -> tuple[str, ...]:
    """Return semantic role names whose title text has insufficient contrast."""
    risks: list[str] = []
    for role_name in (
        "va",
        "rnva",
        "nva",
        "unknown",
        "decision",
        "queue",
        "start_end",
    ):
        role = theme.role(role_name)
        ratio = contrast_ratio(role.title_text, role.fill)
        if ratio is not None and ratio < minimum_ratio:
            risks.append(role_name)
    return tuple(risks)


__all__ = [
    "BUILTIN_THEMES",
    "DEFAULT_THEME",
    "ROLE_NAMES",
    "RenderTheme",
    "ThemeRole",
    "ThemeValidationError",
    "contrast_ratio",
    "resolve_render_theme",
    "theme_contrast_risks",
]
