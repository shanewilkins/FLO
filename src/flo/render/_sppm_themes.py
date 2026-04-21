"""SPPM color themes for value-class node styling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
    return SPPM_THEMES.get(str(name or ""), SPPM_THEMES[_DEFAULT_THEME_NAME])


__all__ = ["SppmThemeName", "SppmNodeStyle", "SppmTheme", "SPPM_THEMES", "resolve_sppm_theme"]
