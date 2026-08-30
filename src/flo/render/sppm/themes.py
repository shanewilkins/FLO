"""Compatibility exports for the legacy SPPM theme model."""

from ..legacy_sppm_themes import (
    SPPM_THEMES,
    SppmNodeStyle,
    SppmTheme,
    SppmThemeName,
    parse_custom_sppm_themes,
    resolve_sppm_theme,
    resolve_sppm_theme_with_custom,
)

__all__ = [
    "SPPM_THEMES",
    "SppmNodeStyle",
    "SppmTheme",
    "SppmThemeName",
    "parse_custom_sppm_themes",
    "resolve_sppm_theme",
    "resolve_sppm_theme_with_custom",
]
