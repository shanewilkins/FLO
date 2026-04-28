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
    assert options.sppm_label_density == "teaching"


def test_explicit_sppm_options_override_profile_defaults():
    options = RenderOptions.from_mapping(
        {
            "diagram": "sppm",
            "sppm_output_profile": "print",
            "orientation": "lr",
            "sppm_label_density": "full",
            "layout_target_columns": 8,
        }
    )
    assert options.orientation == "lr"
    assert options.sppm_label_density == "full"
    assert options.layout_target_columns == 8


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
