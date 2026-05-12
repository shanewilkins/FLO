import pytest

from flo.render.options import RenderOptions


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
