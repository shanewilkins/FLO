"""TOML-based configuration resolution for FLO.

Reads ``diagrams.toml`` adjacent to the source file (or in cwd) and
merges SPPM preset and global config options into the options dict passed
by the caller.  Pure data transformation — no I/O beyond reading the
TOML file itself.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from flo.services.errors import CLIError, EXIT_USAGE


def merge_diagrams_toml_render_defaults(options: dict | None) -> dict:
    """Merge shared and legacy diagrams.toml config into a new options dict.

    CLI-provided values always take precedence over file-based defaults.
    """
    opts = dict(options or {})
    diagrams_toml = _resolve_diagrams_toml_path(opts)
    if diagrams_toml is None:
        return opts

    try:
        data = tomllib.loads(diagrams_toml.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise CLIError(f"Failed to read diagrams.toml: {exc}", code=EXIT_USAGE)

    resolved: dict[str, object] = dict(opts)
    sppm_section = data.get("sppm")
    if not isinstance(sppm_section, dict):
        sppm_section = {}
    config_options = _flatten_sppm_config_options(sppm_section)
    config_options.update(_flatten_shared_render_config_options(data))

    profile_name = (
        str(
            opts.get("sppm_output_profile")
            or config_options.get("sppm_output_profile")
            or "default"
        )
        .strip()
        .lower()
    )
    preset_options = _extract_sppm_preset_options(
        sppm_section=sppm_section, profile_name=profile_name
    )

    for key, value in preset_options.items():
        if key not in resolved:
            resolved[key] = value

    for key, value in config_options.items():
        if key not in resolved:
            resolved[key] = value

    config_keys = sorted(key for key in config_options if key not in opts)
    if config_keys:
        resolved["__diagrams_config_keys__"] = tuple(config_keys)

    return resolved


def merge_diagrams_toml_sppm_defaults(options: dict | None) -> dict:
    """Compatibility alias for the pre-shared-theme config entry point."""
    return merge_diagrams_toml_render_defaults(options)


def _flatten_shared_render_config_options(data: dict) -> dict[str, object]:
    """Flatten central render defaults and the shared theme registry."""
    mapped: dict[str, object] = {}
    themes = data.get("themes")
    if isinstance(themes, dict):
        mapped["themes"] = themes

    render = data.get("render")
    if not isinstance(render, dict):
        return mapped
    _apply_shared_style_options(mapped, render)
    style = render.get("style")
    if isinstance(style, dict):
        _apply_shared_style_options(mapped, style)
    return mapped


def _apply_shared_style_options(
    mapped: dict[str, object], source: dict[str, object]
) -> None:
    for key in ("theme", "background_color", "font_family", "typography_scale"):
        if key in source:
            mapped[key] = source[key]
    canvas = source.get("canvas")
    if isinstance(canvas, dict) and "background" in canvas:
        mapped["background_color"] = canvas["background"]
    typography = source.get("typography")
    if isinstance(typography, dict):
        _apply_typography_options(mapped, typography)


def _apply_typography_options(
    mapped: dict[str, object], typography: dict[str, object]
) -> None:
    if "font_family" in typography:
        mapped["font_family"] = typography["font_family"]
    if "scale" in typography:
        mapped["typography_scale"] = typography["scale"]


def _resolve_diagrams_toml_path(options: dict) -> Path | None:
    source_path = options.get("source_path")
    candidates: list[Path] = []

    if isinstance(source_path, str) and source_path.strip() and source_path != "-":
        source = Path(source_path)
        candidates.append(source.parent / "diagrams.toml")

    candidates.append(Path.cwd() / "diagrams.toml")

    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


def _flatten_sppm_config_options(sppm_section: dict) -> dict[str, object]:
    mapped: dict[str, object] = {}

    def set_if_present(source: dict, src_key: str, dst_key: str) -> None:
        if src_key in source:
            mapped[dst_key] = source[src_key]

    set_if_present(sppm_section, "max_width_px", "layout_max_width_px")
    set_if_present(sppm_section, "target_columns", "layout_target_columns")
    set_if_present(sppm_section, "wrap_layout", "layout_wrap")
    set_if_present(sppm_section, "spacing", "layout_spacing")
    set_if_present(sppm_section, "layout_spacing", "layout_spacing")
    set_if_present(sppm_section, "page_format", "publication_page_format")
    set_if_present(sppm_section, "step_numbering", "sppm_step_numbering")
    set_if_present(sppm_section, "label_density", "sppm_label_density")
    set_if_present(sppm_section, "output_profile", "sppm_output_profile")

    themes_section = sppm_section.get("themes")
    if isinstance(themes_section, dict):
        mapped["sppm_themes"] = themes_section

    text_section = sppm_section.get("text")
    if isinstance(text_section, dict):
        set_if_present(text_section, "wrap_strategy", "sppm_wrap_strategy")
        set_if_present(text_section, "truncation_policy", "sppm_truncation_policy")

        max_label = text_section.get("max_label")
        if isinstance(max_label, dict):
            set_if_present(max_label, "step_name", "sppm_max_label_step_name")
            set_if_present(max_label, "workers", "sppm_max_label_workers")
            set_if_present(max_label, "ctwt", "sppm_max_label_ctwt")

    return mapped


def _extract_sppm_preset_options(
    sppm_section: dict, profile_name: str
) -> dict[str, object]:
    presets = sppm_section.get("presets")
    if not isinstance(presets, dict):
        return {}

    preset = presets.get(profile_name)
    if not isinstance(preset, dict):
        return {}

    mapped: dict[str, object] = {}

    def set_if_present(source: dict, src_key: str, dst_key: str) -> None:
        if src_key in source:
            mapped[dst_key] = source[src_key]

    set_if_present(preset, "orientation", "orientation")
    set_if_present(preset, "max_width_px", "layout_max_width_px")
    set_if_present(preset, "target_columns", "layout_target_columns")
    set_if_present(preset, "wrap_layout", "layout_wrap")
    set_if_present(preset, "spacing", "layout_spacing")
    set_if_present(preset, "layout_spacing", "layout_spacing")
    set_if_present(preset, "page_format", "publication_page_format")
    set_if_present(preset, "label_density", "sppm_label_density")

    text_section = preset.get("text")
    if isinstance(text_section, dict):
        set_if_present(text_section, "wrap_strategy", "sppm_wrap_strategy")
        set_if_present(text_section, "truncation_policy", "sppm_truncation_policy")

        max_label = text_section.get("max_label")
        if isinstance(max_label, dict):
            set_if_present(max_label, "step_name", "sppm_max_label_step_name")
            set_if_present(max_label, "workers", "sppm_max_label_workers")
            set_if_present(max_label, "ctwt", "sppm_max_label_ctwt")

    return mapped
