"""SPPM color themes for value-class node styling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

SppmThemeName = Literal["default", "print", "monochrome"]


@dataclass(frozen=True)
class SppmNodeStyle:
    """Fill and border colors for a single node category."""

    fill: str
    border: str


@dataclass(frozen=True)
class SppmTheme:
    """Complete color theme for an SPPM diagram."""

    va: SppmNodeStyle
    rnva: SppmNodeStyle
    nva: SppmNodeStyle
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
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#9E9E9E"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
    ),
    "print": SppmTheme(
        # High-contrast fills that survive black-and-white printing
        va=SppmNodeStyle(fill="#D5E8D4", border="#1A5C1A"),
        rnva=SppmNodeStyle(fill="#DAE8FC", border="#23527C"),
        nva=SppmNodeStyle(fill="#F8CECC", border="#8B0000"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#555555"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#000000"),
    ),
    "monochrome": SppmTheme(
        # Grayscale only — suitable for print/export where color is unavailable
        va=SppmNodeStyle(fill="#CCCCCC", border="#333333"),
        rnva=SppmNodeStyle(fill="#888888", border="#333333"),
        nva=SppmNodeStyle(fill="#444444", border="#000000"),
        unknown=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
        start_end=SppmNodeStyle(fill="#FFFFFF", border="#333333"),
    ),
}

_DEFAULT_THEME_NAME: SppmThemeName = "default"


def resolve_sppm_theme(name: str | None) -> SppmTheme:
    """Return the named theme, falling back to default for unknown names."""
    return resolve_sppm_theme_with_custom(name=name, custom_themes=None)


def resolve_sppm_theme_with_custom(name: str | None, custom_themes: Mapping[str, SppmTheme] | None) -> SppmTheme:
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
    for key in ("va", "rnva", "nva", "unknown", "start_end"):
        style = _parse_style_definition(value, key)
        if style is None:
            return None
        styles[key] = style

    return SppmTheme(
        va=styles["va"],
        rnva=styles["rnva"],
        nva=styles["nva"],
        unknown=styles["unknown"],
        start_end=styles["start_end"],
    )


def _parse_style_definition(theme_value: Mapping[str, Any], style_name: str) -> SppmNodeStyle | None:
    nested = theme_value.get(style_name)
    if isinstance(nested, Mapping):
        return _parse_node_style(nested)

    fill_key = f"{style_name}_fill"
    border_key = f"{style_name}_border"
    if fill_key in theme_value or border_key in theme_value:
        return _parse_node_style({"fill": theme_value.get(fill_key), "border": theme_value.get(border_key)})
    return None


def _parse_node_style(value: Mapping[str, Any]) -> SppmNodeStyle | None:
    fill = value.get("fill")
    border = value.get("border")
    if not isinstance(fill, str) or not fill.strip():
        return None
    if not isinstance(border, str) or not border.strip():
        return None
    return SppmNodeStyle(fill=fill.strip(), border=border.strip())


__all__ = [
    "SppmThemeName",
    "SppmNodeStyle",
    "SppmTheme",
    "SPPM_THEMES",
    "parse_custom_sppm_themes",
    "resolve_sppm_theme",
    "resolve_sppm_theme_with_custom",
]
