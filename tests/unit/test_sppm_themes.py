from __future__ import annotations

import pytest

from flo.render._sppm_themes import (
    SPPM_THEMES,
    SppmNodeStyle,
    SppmTheme,
    parse_custom_sppm_themes,
    resolve_sppm_theme,
    resolve_sppm_theme_with_custom,
)


@pytest.mark.parametrize(
    ("value_class", "expected_attr"),
    [
        ("VA", "va"),
        ("RNVA", "rnva"),
        ("NVA", "nva"),
        ("unknown", "unknown"),
        (None, "unknown"),
        ("va", "unknown"),
        ("other", "unknown"),
    ],
)
def test_theme_style_for_maps_known_classes_and_falls_back(
    value_class: str | None,
    expected_attr: str,
) -> None:
    theme = SPPM_THEMES["default"]

    style = theme.style_for(value_class)

    assert style == getattr(theme, expected_attr)


def test_resolve_sppm_theme_with_custom_overrides_builtin() -> None:
    custom_theme = SppmTheme(
        va=SppmNodeStyle(fill="#101010", border="#202020"),
        rnva=SppmNodeStyle(fill="#303030", border="#404040"),
        nva=SppmNodeStyle(fill="#505050", border="#606060"),
        decision=SppmNodeStyle(fill="#707070", border="#808080"),
        unknown=SppmNodeStyle(fill="#909090", border="#A0A0A0"),
        start_end=SppmNodeStyle(fill="#B0B0B0", border="#C0C0C0"),
    )

    resolved = resolve_sppm_theme_with_custom(
        name="default",
        custom_themes={"default": custom_theme},
    )

    assert resolved == custom_theme


def test_resolve_sppm_theme_with_custom_trims_name_and_falls_back_to_default() -> None:
    custom_theme = SppmTheme(
        va=SppmNodeStyle(fill="#111111", border="#222222"),
        rnva=SppmNodeStyle(fill="#333333", border="#444444"),
        nva=SppmNodeStyle(fill="#555555", border="#666666"),
        decision=SppmNodeStyle(fill="#777777", border="#888888"),
        unknown=SppmNodeStyle(fill="#999999", border="#AAAAAA"),
        start_end=SppmNodeStyle(fill="#BBBBBB", border="#CCCCCC"),
    )

    resolved_custom = resolve_sppm_theme_with_custom(
        name="  house  ",
        custom_themes={"house": custom_theme},
    )
    fallback = resolve_sppm_theme_with_custom(name="missing", custom_themes=None)

    assert resolved_custom == custom_theme
    assert fallback == SPPM_THEMES["default"]


def test_resolve_sppm_theme_handles_unknown_name() -> None:
    assert resolve_sppm_theme("missing") == SPPM_THEMES["default"]


def test_parse_custom_sppm_themes_supports_nested_and_flat_definitions() -> None:
    parsed = parse_custom_sppm_themes(
        {
            "nested": {
                "va": {"fill": "#111", "border": "#222"},
                "rnva": {"fill": "#333", "border": "#444"},
                "nva": {"fill": "#555", "border": "#666"},
                "decision": {"fill": "#777", "border": "#888"},
                "unknown": {"fill": "#999", "border": "#AAA"},
                "start_end": {"fill": "#BBB", "border": "#CCC"},
            },
            "flat": {
                "va_fill": "#101",
                "va_border": "#202",
                "rnva_fill": "#303",
                "rnva_border": "#404",
                "nva_fill": "#505",
                "nva_border": "#606",
                "decision_fill": "#707",
                "decision_border": "#808",
                "unknown_fill": "#909",
                "unknown_border": "#A0A",
                "start_end_fill": "#B0B",
                "start_end_border": "#C0C",
            },
            "invalid": {
                "va": {"fill": "#111"},
                "rnva": {"fill": "#333", "border": "#444"},
                "nva": {"fill": "#555", "border": "#666"},
                "decision": {"fill": "#777", "border": "#888"},
                "unknown": {"fill": "#999", "border": "#AAA"},
                "start_end": {"fill": "#BBB", "border": "#CCC"},
            },
        }
    )

    assert set(parsed.keys()) == {"nested", "flat"}
    assert parsed["nested"].va == SppmNodeStyle(fill="#111", border="#222")
    assert parsed["flat"].decision == SppmNodeStyle(fill="#707", border="#808")


def test_parse_custom_sppm_themes_non_mapping_returns_empty() -> None:
    assert parse_custom_sppm_themes(None) == {}
    assert parse_custom_sppm_themes(["bad"]) == {}
