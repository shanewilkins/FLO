"""SPPM color themes for value-class node styling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

SppmThemeName = Literal["default", "flatly", "print", "monochrome"]


@dataclass(frozen=True)
class SppmNodeStyle:
    """Fill and border colors for a single node category."""

    fill: str
    border: str
    title_fill: str = "#0f172a"
    info_fill: str = "#475569"


@dataclass(frozen=True)
class SppmTheme:
    """Complete color theme for an SPPM diagram."""

    va: SppmNodeStyle
    rnva: SppmNodeStyle
    nva: SppmNodeStyle
    decision: SppmNodeStyle
    queue: SppmNodeStyle
    unknown: SppmNodeStyle
    start_end: SppmNodeStyle

    def style_for(self, value_class: str | None) -> SppmNodeStyle:
        """Return the node style for the given value_class string (or unknown)."""
        mapping = {
            "VA": self.va,
            "RNVA": self.rnva,
            "NVA": self.nva,
            "unknown": self.unknown,
        }
        return mapping.get(value_class or "", self.unknown)


SPPM_THEMES: dict[str, SppmTheme] = {
    "default": SppmTheme(
        va=SppmNodeStyle(fill="#81C784", border="#2E7D32"),
        rnva=SppmNodeStyle(fill="#FFF176", border="#F9A825"),
        nva=SppmNodeStyle(fill="#EF9A9A", border="#C62828"),
        decision=SppmNodeStyle(fill="#E3EEF7", border="#285B8F"),
        queue=SppmNodeStyle(fill="#FFB74D", border="#E65100"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#9E9E9E"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
    ),
    "flatly": SppmTheme(
        va=SppmNodeStyle(fill="#D1F2EB", border="#18BC9C", title_fill="#0A4B3E"),
        rnva=SppmNodeStyle(fill="#FDEBD0", border="#F39C12", title_fill="#613E07"),
        nva=SppmNodeStyle(fill="#FADBD8", border="#E74C3C", title_fill="#5C1E18"),
        decision=SppmNodeStyle(fill="#D5D8DC", border="#2C3E50", title_fill="#121920"),
        queue=SppmNodeStyle(fill="#F39C12", border="#C27D0E", title_fill="#2C3E50"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#95A5A6", title_fill="#2C3E50"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#2C3E50", title_fill="#2C3E50"),
    ),
    "print": SppmTheme(
        # High-contrast fills that survive black-and-white printing
        va=SppmNodeStyle(fill="#D5E8D4", border="#1A5C1A"),
        rnva=SppmNodeStyle(fill="#DAE8FC", border="#23527C"),
        nva=SppmNodeStyle(fill="#F8CECC", border="#8B0000"),
        decision=SppmNodeStyle(fill="#FFFFFF", border="#000000"),
        queue=SppmNodeStyle(fill="#FFFFFF", border="#000000"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#555555"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#000000"),
    ),
    "monochrome": SppmTheme(
        # Grayscale only — suitable for print/export where color is unavailable
        va=SppmNodeStyle(fill="#CCCCCC", border="#333333"),
        rnva=SppmNodeStyle(fill="#888888", border="#333333"),
        nva=SppmNodeStyle(fill="#444444", border="#000000"),
        decision=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
        queue=SppmNodeStyle(fill="#777777", border="#000000"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
    ),
}

_DEFAULT_THEME_NAME: SppmThemeName = "default"


def resolve_sppm_theme(name: str | None) -> SppmTheme:
    """Return the named theme, falling back to default for unknown names."""
    return resolve_sppm_theme_with_custom(name=name, custom_themes=None)


def resolve_sppm_theme_with_custom(
    name: str | None, custom_themes: Mapping[str, SppmTheme] | None
) -> SppmTheme:
    """Return a built-in or custom theme, falling back to default when missing."""
    registry: dict[str, SppmTheme] = dict(SPPM_THEMES)
    if custom_themes:
        for theme_name, theme in custom_themes.items():
            registry[str(theme_name).strip()] = theme

    theme_name = str(name or "").strip()
    return registry.get(theme_name, registry[_DEFAULT_THEME_NAME])


def parse_custom_sppm_themes(value: Any) -> dict[str, SppmTheme]:
    """Parse custom theme definitions from a mapping-like config value."""
    if not isinstance(value, Mapping):
        return {}

    parsed: dict[str, SppmTheme] = {}
    for theme_name, theme_value in value.items():
        theme = _parse_theme_definition(theme_value)
        if theme is not None:
            parsed[str(theme_name).strip()] = theme
    return parsed


def _parse_theme_definition(value: Any) -> SppmTheme | None:
    if not isinstance(value, Mapping):
        return None

    styles: dict[str, SppmNodeStyle] = {}
    for key in (
        "va",
        "rnva",
        "nva",
        "decision",
        "unknown",
        "start_end",
    ):
        style = _parse_style_definition(value, key)
        if style is None:
            return None
        styles[key] = style
    styles["queue"] = _parse_style_definition(value, "queue") or styles["rnva"]

    return SppmTheme(
        va=styles["va"],
        rnva=styles["rnva"],
        nva=styles["nva"],
        decision=styles["decision"],
        queue=styles["queue"],
        unknown=styles["unknown"],
        start_end=styles["start_end"],
    )


def _parse_style_definition(
    theme_value: Mapping[str, Any], style_name: str
) -> SppmNodeStyle | None:
    nested = theme_value.get(style_name)
    if isinstance(nested, Mapping):
        return _parse_node_style(nested)

    fill_key = f"{style_name}_fill"
    border_key = f"{style_name}_border"
    if fill_key in theme_value or border_key in theme_value:
        return _parse_node_style(
            {"fill": theme_value.get(fill_key), "border": theme_value.get(border_key)}
        )
    return None


def _parse_node_style(value: Mapping[str, Any]) -> SppmNodeStyle | None:
    fill = value.get("fill")
    border = value.get("border")
    if not isinstance(fill, str) or not fill.strip():
        return None
    if not isinstance(border, str) or not border.strip():
        return None
    title_fill = value.get("title_fill", "#0f172a")
    info_fill = value.get("info_fill", "#475569")
    if not isinstance(title_fill, str) or not title_fill.strip():
        return None
    if not isinstance(info_fill, str) or not info_fill.strip():
        return None
    return SppmNodeStyle(
        fill=fill.strip(),
        border=border.strip(),
        title_fill=title_fill.strip(),
        info_fill=info_fill.strip(),
    )


__all__ = [
    "SppmThemeName",
    "SppmNodeStyle",
    "SppmTheme",
    "SPPM_THEMES",
    "parse_custom_sppm_themes",
    "resolve_sppm_theme",
    "resolve_sppm_theme_with_custom",
]
