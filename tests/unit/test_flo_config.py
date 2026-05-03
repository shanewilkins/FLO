from pathlib import Path

import pytest

from flo.core._flo_config import (
    _extract_sppm_preset_options,
    _flatten_sppm_config_options,
    _resolve_diagrams_toml_path,
    merge_diagrams_toml_sppm_defaults,
)
from flo.services.errors import CLIError, EXIT_USAGE


def test_merge_diagrams_toml_returns_original_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = {"diagram": "sppm", "layout_spacing": "compact"}
    out = merge_diagrams_toml_sppm_defaults(options)
    assert out == options
    assert out is not options


def test_merge_diagrams_toml_prefers_source_dir_and_preserves_cli_overrides(tmp_path, monkeypatch):
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


def test_resolve_diagrams_toml_path_handles_dash_source_and_resolve_error(tmp_path, monkeypatch):
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


def _sample_sppm_config() -> dict:
    return {
        "max_width_px": 1200,
        "target_columns": 7,
        "wrap_layout": "auto",
        "spacing": "standard",
        "layout_spacing": "compact",
        "step_numbering": "node",
        "label_density": "compact",
        "output_profile": "book",
        "text": {
            "wrap_strategy": "balanced",
            "truncation_policy": "clip",
            "max_label": {"step_name": 48, "workers": 24, "ctwt": 18},
        },
        "presets": {
            "book": {
                "orientation": "tb",
                "max_width_px": 900,
                "target_columns": 5,
                "wrap_layout": "off",
                "spacing": "compact",
                "layout_spacing": "standard",
                "label_density": "teaching",
                "text": {
                    "wrap_strategy": "word",
                    "truncation_policy": "ellipsis",
                    "max_label": {"step_name": 30, "workers": 15, "ctwt": 12},
                },
            }
        },
    }


def test_flatten_helper_maps_nested_text_options():
    sppm = _sample_sppm_config()

    flattened = _flatten_sppm_config_options(sppm)
    assert flattened["layout_max_width_px"] == 1200
    assert flattened["layout_target_columns"] == 7
    assert flattened["layout_wrap"] == "auto"
    assert flattened["layout_spacing"] == "compact"
    assert flattened["sppm_step_numbering"] == "node"
    assert flattened["sppm_label_density"] == "compact"
    assert flattened["sppm_output_profile"] == "book"
    assert flattened["sppm_wrap_strategy"] == "balanced"
    assert flattened["sppm_truncation_policy"] == "clip"
    assert flattened["sppm_max_label_step_name"] == 48
    assert flattened["sppm_max_label_workers"] == 24
    assert flattened["sppm_max_label_ctwt"] == 18


def test_preset_helper_maps_profile_specific_options():
    sppm = _sample_sppm_config()

    preset = _extract_sppm_preset_options(sppm, "book")
    assert preset["orientation"] == "tb"
    assert preset["layout_max_width_px"] == 900
    assert preset["layout_target_columns"] == 5
    assert preset["layout_wrap"] == "off"
    assert preset["layout_spacing"] == "standard"
    assert preset["sppm_label_density"] == "teaching"
    assert preset["sppm_wrap_strategy"] == "word"
    assert preset["sppm_truncation_policy"] == "ellipsis"
    assert preset["sppm_max_label_step_name"] == 30
    assert preset["sppm_max_label_workers"] == 15
    assert preset["sppm_max_label_ctwt"] == 12


def test_extract_preset_returns_empty_for_missing_or_invalid_shapes():
    assert _extract_sppm_preset_options({}, "book") == {}
    assert _extract_sppm_preset_options({"presets": []}, "book") == {}
    assert _extract_sppm_preset_options({"presets": {"book": "bad"}}, "book") == {}
