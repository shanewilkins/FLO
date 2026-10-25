from pathlib import Path

import pytest

from flo.app._flo_config import (
    _resolve_diagrams_toml_path,
    merge_diagrams_toml_sppm_defaults,
)
from flo.errors import EXIT_USAGE, CLIError


def test_merge_diagrams_toml_returns_original_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = {"diagram": "sppm", "layout_spacing": "compact"}
    out = merge_diagrams_toml_sppm_defaults(options)
    assert out == options
    assert out is not options


def test_merge_diagrams_toml_prefers_source_dir_and_preserves_cli_overrides(
    tmp_path, monkeypatch
):
    source_dir = tmp_path / "srcdir"
    source_dir.mkdir()
    model_path = source_dir / "demo.flo"
    model_path.write_text("spec_version: '0.1'\n", encoding="utf-8")

    (tmp_path / "diagrams.toml").write_text(
        "[sppm]\nlayout_spacing='standard'\n",
        encoding="utf-8",
    )
    (source_dir / "diagrams.toml").write_text(
        "\n".join(
            [
                "[sppm]",
                "output_profile = 'book'",
                "layout_spacing = 'compact'",
                "[sppm.presets.book]",
                "orientation = 'tb'",
                "target_columns = 6",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    out = merge_diagrams_toml_sppm_defaults(
        {
            "source_path": str(model_path),
            "orientation": "lr",  # explicit CLI value must win
            "diagram": "sppm",
        }
    )

    assert out["orientation"] == "lr"
    assert out["layout_spacing"] == "compact"
    assert out["layout_target_columns"] == 6
    assert out["sppm_output_profile"] == "book"


def test_merge_diagrams_toml_loads_custom_themes(tmp_path, monkeypatch):
    model_path = tmp_path / "demo.flo"
    model_path.write_text("spec_version: '0.1'\n", encoding="utf-8")

    (tmp_path / "diagrams.toml").write_text(
        "\n".join(
            [
                "[sppm]",
                "output_profile = 'default'",
                "",
                "[sppm.themes.sunrise.va]",
                "fill = '#FFF3B0'",
                "border = '#E09F3E'",
                "",
                "[sppm.themes.sunrise.rnva]",
                "fill = '#FFD6A5'",
                "border = '#F77F00'",
                "",
                "[sppm.themes.sunrise.nva]",
                "fill = '#FFADAD'",
                "border = '#D00000'",
                "",
                "[sppm.themes.sunrise.decision]",
                "fill = '#FFF8E1'",
                "border = '#B28704'",
                "",
                "[sppm.themes.sunrise.unknown]",
                "fill = '#FFFFFF'",
                "border = '#6C757D'",
                "",
                "[sppm.themes.sunrise.start_end]",
                "fill = '#FFFFFF'",
                "border = '#343A40'",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    out = merge_diagrams_toml_sppm_defaults(
        {"source_path": str(model_path), "diagram": "sppm"}
    )

    assert out["sppm_themes"]["sunrise"]["va"]["fill"] == "#FFF3B0"
    assert out["sppm_themes"]["sunrise"]["decision"]["border"] == "#B28704"
    assert out["sppm_themes"]["sunrise"]["start_end"]["border"] == "#343A40"


def test_merge_diagrams_toml_loads_shared_registry_and_render_defaults(
    tmp_path, monkeypatch
):
    model_path = tmp_path / "demo.flo"
    model_path.write_text("spec_version: '0.1'\n", encoding="utf-8")
    (tmp_path / "diagrams.toml").write_text(
        "\n".join(
            [
                "[render]",
                "theme = 'book_house'",
                "[render.style.canvas]",
                "background = '#F4F0FF'",
                "[render.style.typography]",
                "font_family = ['Avenir Next', 'Arial']",
                "scale = 1.1",
                "[themes.book_house]",
                "extends = 'default'",
                "[themes.book_house.roles.va]",
                "fill = '#B8E6C1'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    out = merge_diagrams_toml_sppm_defaults({"source_path": str(model_path)})

    assert out["theme"] == "book_house"
    assert out["background_color"] == "#F4F0FF"
    assert out["font_family"] == ["Avenir Next", "Arial"]
    assert out["typography_scale"] == 1.1
    assert out["themes"]["book_house"]["roles"]["va"]["fill"] == "#B8E6C1"


def test_merge_diagrams_toml_invalid_toml_raises_clierror(tmp_path, monkeypatch):
    (tmp_path / "diagrams.toml").write_text("[sppm\nnot valid", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(CLIError) as exc:
        merge_diagrams_toml_sppm_defaults({})

    assert exc.value.code == EXIT_USAGE
    assert "Failed to read diagrams.toml" in str(exc.value)


def test_merge_diagrams_toml_oserror_raises_clierror(tmp_path, monkeypatch):
    cfg = tmp_path / "diagrams.toml"
    cfg.write_text("[sppm]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    original_read_text = Path.read_text

    def _boom(self: Path, *args, **kwargs):
        if self == cfg:
            raise OSError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _boom)

    with pytest.raises(CLIError) as exc:
        merge_diagrams_toml_sppm_defaults({})

    assert exc.value.code == EXIT_USAGE
    assert "permission denied" in str(exc.value)


def test_resolve_diagrams_toml_path_handles_dash_source_and_resolve_error(
    tmp_path, monkeypatch
):
    cfg = tmp_path / "diagrams.toml"
    cfg.write_text("[sppm]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    original_resolve = Path.resolve
    calls = {"count": 0}

    def flaky_resolve(self: Path, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("transient")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", flaky_resolve)

    resolved = _resolve_diagrams_toml_path({"source_path": "-"})
    assert resolved is None


@pytest.mark.parametrize(
    ("content", "field"),
    [
        ("sppm = []", "sppm"),
        ("[sppm]\ntext = 'bad'", "sppm.text"),
        ("[sppm.text]\nmax_label = []", "sppm.text.max_label"),
        (
            "[sppm]\noutput_profile = 'book'\n[sppm.presets]\nbook = false",
            "sppm.presets.book",
        ),
        ("[sppm]\ntarget_columns = true", "sppm.target_columns"),
        ("[sppm]\ntarget_columns = 1.5", "sppm.target_columns"),
        ("[sppm]\ntarget_columns = 0", "sppm.target_columns"),
        ("[sppm]\nmax_width_px = false", "sppm.max_width_px"),
        ("[sppm]\nmax_width_px = inf", "sppm.max_width_px"),
        ("[sppm.text.max_label]\nworkers = -1", "sppm.text.max_label.workers"),
        ("[render]\nstyle = []", "render.style"),
        ("[render.style]\ncanvas = 'white'", "render.style.canvas"),
        ("[render.typography]\nscale = true", "render.typography.scale"),
        ("[render]\nfont_family = ['Arial', 5]", "render.font_family"),
        ("[themes]\nbroken = false", "themes.broken"),
    ],
)
def test_invalid_config_reports_authored_field_path(
    tmp_path, monkeypatch, content, field
):
    (tmp_path / "diagrams.toml").write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(CLIError) as exc:
        merge_diagrams_toml_sppm_defaults({})

    assert exc.value.code == EXIT_USAGE
    assert exc.value.error_stage == "option_validation"
    assert "Invalid diagrams.toml" in str(exc.value)
    assert field in str(exc.value)
    assert "retry" in str(exc.value)


def test_config_models_preserve_aliases_and_authored_fields_only(tmp_path, monkeypatch):
    from flo.render.options import RenderOptions

    (tmp_path / "diagrams.toml").write_text(
        """[sppm]
max_width_px = '12in'
target_columns = '6'
wrap_layout = true
spacing = 'tight'
label_density = 'teach'
[sppm.text]
wrap_strategy = 'character'
truncation_policy = 'cut'
[sppm.text.max_label]
step_name = '48'
[render]
theme = 'mono'
[extension]
arbitrary = true
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    merged = merge_diagrams_toml_sppm_defaults({})
    assert "orientation" not in merged
    assert "sppm_output_profile" not in merged
    assert "themes" not in merged
    assert "extension" not in merged
    resolved = RenderOptions.from_mapping(merged)
    assert resolved.layout_max_width_px == 1152
    assert resolved.layout_target_columns == 6
    assert resolved.layout_wrap == "auto"
    assert resolved.layout_spacing == "compact"
    assert resolved.sppm_label_density == "teaching"
    assert resolved.sppm_wrap_strategy == "hard"
    assert resolved.sppm_truncation_policy == "clip"
    assert resolved.sppm_max_label_step_name == 48
    assert resolved.resolved_theme.name == "monochrome"


def test_config_validation_collects_errors_without_echoing_input(tmp_path, monkeypatch):
    (tmp_path / "diagrams.toml").write_text(
        "[sppm]\ntarget_columns = 'private-value'\nmax_width_px = false",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(CLIError) as exc:
        merge_diagrams_toml_sppm_defaults({})

    message = str(exc.value)
    assert "sppm.target_columns" in message
    assert "sppm.max_width_px" in message
    assert "private-value" not in message


def test_config_validation_ignores_unselected_presets(tmp_path, monkeypatch):
    (tmp_path / "diagrams.toml").write_text(
        "[sppm.presets.print]\ntarget_columns = false", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    merged = merge_diagrams_toml_sppm_defaults({"sppm_output_profile": "book"})
    assert "layout_target_columns" not in merged


def test_config_models_preserve_existing_preset_and_style_merge_order(
    tmp_path, monkeypatch
):
    (tmp_path / "diagrams.toml").write_text(
        """[sppm]
output_profile = 'book'
target_columns = 7
[sppm.presets.book]
target_columns = 5
orientation = 'tb'
[render]
background_color = '#111111'
[render.canvas]
background = '#222222'
[render.style]
background_color = '#333333'
[render.style.canvas]
background = '#444444'
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    options = {"orientation": "lr"}

    merged = merge_diagrams_toml_sppm_defaults(options)

    # Retain current merging, including preset priority over global SPPM fields.
    assert merged["layout_target_columns"] == 5
    assert merged["orientation"] == "lr"
    assert merged["background_color"] == "#444444"
    assert options == {"orientation": "lr"}
    assert (
        merge_diagrams_toml_sppm_defaults({"layout_target_columns": 9})[
            "layout_target_columns"
        ]
        == 9
    )


@pytest.mark.parametrize("value", ["6", "6.0", "'6'"])
def test_config_positive_integers_accept_lossless_conversion(
    tmp_path, monkeypatch, value
):
    (tmp_path / "diagrams.toml").write_text(f"[sppm]\ntarget_columns = {value}")
    monkeypatch.chdir(tmp_path)
    assert merge_diagrams_toml_sppm_defaults({})["layout_target_columns"] == 6


def test_cli_override_bypasses_invalid_file_default(tmp_path, monkeypatch):
    (tmp_path / "diagrams.toml").write_text("[sppm]\ntarget_columns = false")
    monkeypatch.chdir(tmp_path)
    assert (
        merge_diagrams_toml_sppm_defaults({"layout_target_columns": 8})[
            "layout_target_columns"
        ]
        == 8
    )


def test_selected_preset_bypasses_invalid_global_value(tmp_path, monkeypatch):
    (tmp_path / "diagrams.toml").write_text(
        "[sppm]\ntarget_columns = false\n[sppm.presets.book]\ntarget_columns = 6"
    )
    monkeypatch.chdir(tmp_path)
    assert (
        merge_diagrams_toml_sppm_defaults({"sppm_output_profile": "book"})[
            "layout_target_columns"
        ]
        == 6
    )


@pytest.mark.parametrize(
    ("profile", "preset"), [("", "default"), ("book.with.dot", "book.with.dot")]
)
def test_preset_names_are_literal_and_empty_profile_uses_default(
    tmp_path, monkeypatch, profile, preset
):
    (tmp_path / "diagrams.toml").write_text(
        f"[sppm]\noutput_profile = '{profile}'\n[sppm.presets.'{preset}']\ntarget_columns = 6"
    )
    monkeypatch.chdir(tmp_path)
    assert merge_diagrams_toml_sppm_defaults({})["layout_target_columns"] == 6
