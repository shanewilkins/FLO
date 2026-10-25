import pytest

from flo.render.options import RenderOptions


def test_value_stream_is_a_public_diagram_option() -> None:
    assert RenderOptions.from_mapping({"diagram": "value_stream"}).diagram == (
        "value_stream"
    )


def test_sppm_output_profile_book_applies_defaults():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "book",
        }
    )
    assert options.orientation == "lr"
    assert options.layout_wrap == "auto"
    assert options.layout_fit == "fit-preferred"
    assert options.layout_max_width_px == 1200
    assert options.layout_target_columns == 6
    assert options.publication_page_format == "letter"
    assert options.sppm_label_density == "compact"


def test_sppm_output_profile_print_applies_tb_defaults():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "print",
        }
    )
    assert options.orientation == "tb"
    assert options.layout_wrap == "auto"
    assert options.layout_fit == "fit-strict"
    assert options.layout_max_width_px == 1000
    assert options.layout_target_columns == 5
    assert options.publication_page_format == "a4"
    assert options.sppm_label_density == "teaching"


def test_explicit_sppm_options_override_profile_defaults():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "print",
            "orientation": "lr",
            "publication_page_format": "legal",
            "sppm_label_density": "full",
            "layout_target_columns": 8,
        }
    )
    assert options.orientation == "lr"
    assert options.publication_page_format == "legal"
    assert options.sppm_label_density == "full"
    assert options.layout_target_columns == 8


def test_layout_max_width_dimension_units_normalize_to_pixels():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "layout_max_width_px": "8.5in",
        }
    )

    assert options.layout_max_width is not None
    assert options.layout_max_width.unit == "in"
    assert options.layout_max_width.value == 8.5
    assert options.layout_max_width_px == 816


def test_layout_max_width_cm_dimension_rounds_consistently():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "layout_max_width_px": "10cm",
        }
    )

    assert options.layout_max_width is not None
    assert options.layout_max_width.unit == "cm"
    assert options.layout_max_width_px == 378


def test_layout_max_width_mm_dimension_rounds_consistently():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "layout_max_width_px": "210mm",
        }
    )

    assert options.layout_max_width is not None
    assert options.layout_max_width.unit == "mm"
    assert options.layout_max_width_px == 794


def test_geometry_dimensions_and_overflow_policy_normalize_from_mapping():
    options = RenderOptions.from_mapping(
        {
            "layout_width": "210mm",
            "layout_height": "11in",
            "layout_overflow": "scale",
        }
    )

    assert options.layout_width_px == 794
    assert options.layout_height_px == 1056
    assert options.layout_overflow == "scale"


def test_geometry_overflow_defaults_to_safe_fit():
    assert RenderOptions().layout_overflow == "safe-fit"


def test_default_diagram_is_sppm():
    assert RenderOptions().diagram == "sppm"
    assert RenderOptions.from_mapping({}).diagram == "sppm"


@pytest.mark.parametrize("value", ["0cm", "12pt", "wide"])
def test_layout_max_width_rejects_invalid_dimensions(value: str):
    with pytest.raises(ValueError, match="layout_max_width_px"):
        RenderOptions.from_mapping(
            {
                "diagram": "sppm",
                "layout_max_width_px": value,
            }
        )


def test_explicit_layout_fit_overrides_profile_defaults():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "print",
            "layout_fit": "fit-preferred",
        }
    )
    assert options.layout_fit == "fit-preferred"


def test_layout_spacing_defaults_to_standard():
    options = RenderOptions.from_mapping({"diagram": "sppm"})
    assert options.layout_spacing == "standard"
    assert options.subprocess_view == "parent_only"
    assert options.sppm_projection == "top_level"


def test_layout_spacing_compact_is_respected():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "layout_spacing": "compact",
        }
    )
    assert options.layout_spacing == "compact"


def test_spaghetti_strict_spatial_is_explicit_and_defaults_false():
    assert RenderOptions().spaghetti_strict_spatial is False
    assert (
        RenderOptions.from_mapping(
            {"spaghetti_strict_spatial": True}
        ).spaghetti_strict_spatial
        is True
    )


def test_layout_spacing_tight_alias_maps_to_compact():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "layout_spacing": "tight",
        }
    )
    assert options.layout_spacing == "compact"


def test_sppm_footer_render_inputs_parse_from_mapping():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_footer_metrics": {"Lead Time": "24 min", "Queue": "7 min"},
            "sppm_footer_notes": ["Draft for review", "Confidential"],
        }
    )

    assert options.sppm_footer_metrics == (("Lead Time", "24 min"), ("Queue", "7 min"))
    assert options.sppm_footer_notes == ("Draft for review", "Confidential")


def test_sppm_legend_and_caption_aliases_parse_into_footer_inputs():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_legend_items": {"Queue": "7 min", "Rework": "8%"},
            "sppm_caption": "Draft for review",
        }
    )

    assert options.sppm_footer_metrics == (("Queue", "7 min"), ("Rework", "8%"))
    assert options.sppm_footer_notes == ("Draft for review",)


def test_sppm_projection_and_focus_parse_from_mapping():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_projection": "child-map",
            "sppm_focus_subprocess": " prep ",
        }
    )

    assert options.sppm_projection == "child_map"
    assert options.sppm_focus_subprocess == "prep"
    assert options.subprocess_view == "parent_only"


def test_sppm_no_header_flag_disables_header_band():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "no_header": True,
        }
    )
    assert options.sppm_show_header is False
    assert options.sppm_show_footer is True


def test_sppm_no_footer_flag_disables_footer_band():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "no_footer": True,
        }
    )
    assert options.sppm_show_header is True
    assert options.sppm_show_footer is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"orientation": "top_to_bottom"}, {"orientation": "tb"}),
        ({"layout_wrap": True}, {"layout_wrap": "auto"}),
        ({"layout_fit": "strict"}, {"layout_fit": "fit-strict"}),
        ({"layout_spacing": "tight"}, {"layout_spacing": "compact"}),
        ({"spaghetti_channel": "materials"}, {"spaghetti_channel": "material"}),
        ({"spaghetti_people_mode": "per_worker"}, {"spaghetti_people_mode": "worker"}),
        ({"profile": "analysis"}, {"spaghetti_people_mode": "worker"}),
        (
            {"subprocess_view": "child-map"},
            {"subprocess_view": "child_map", "sppm_projection": "child_map"},
        ),
        ({"sppm_wrap_strategy": "character"}, {"sppm_wrap_strategy": "hard"}),
        ({"sppm_truncation_policy": "disabled"}, {"sppm_truncation_policy": "none"}),
        ({"layout_target_columns": "6"}, {"layout_target_columns": 6}),
        ({"layout_target_columns": 6.0}, {"layout_target_columns": 6}),
    ],
)
def test_shared_model_preserves_aliases_through_cli_and_render_boundaries(
    raw, expected
):
    from flo.app._option_validation import validate_render_options

    original = dict(raw)
    direct = RenderOptions.from_mapping(raw)
    via_application = RenderOptions.from_mapping(validate_render_options(raw))

    for key, value in expected.items():
        assert getattr(direct, key) == value
        assert getattr(via_application, key) == value
    assert raw == original


@pytest.mark.parametrize(
    "raw",
    [
        {"layout_target_columns": True},
        {"layout_target_columns": 1.5},
        {"layout_width": "0cm"},
        {"publication_page_format": "unknown"},
        {"typography_scale": True},
        {"themes": {"bad": False}},
        {"orientation": []},
        {"sppm_output_profile": {}},
        {"subprocess_view": []},
    ],
)
def test_shared_model_rejects_malformed_values_at_both_boundaries(raw):
    from flo.app._option_validation import validate_render_options
    from flo.errors import CLIError

    key = next(iter(raw))
    with pytest.raises(ValueError, match=key):
        RenderOptions.from_mapping(raw)
    with pytest.raises(CLIError, match=key):
        validate_render_options(raw)
