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


def merge_diagrams_toml_sppm_defaults(options: dict | None) -> dict:
    """Merge diagrams.toml SPPM config into *options*, returning a new dict.

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

    sppm_section = data.get("sppm")
    if not isinstance(sppm_section, dict):
        return opts

    resolved: dict[str, object] = dict(opts)
    config_options = _flatten_sppm_config_options(sppm_section)

    profile_name = str(opts.get("sppm_output_profile") or config_options.get("sppm_output_profile") or "default").strip().lower()
    preset_options = _extract_sppm_preset_options(sppm_section=sppm_section, profile_name=profile_name)

    for key, value in preset_options.items():
        if key not in resolved:
            resolved[key] = value

    for key, value in config_options.items():
        if key not in resolved:
            resolved[key] = value

    return resolved


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
    set_if_present(sppm_section, "step_numbering", "sppm_step_numbering")
    set_if_present(sppm_section, "label_density", "sppm_label_density")
    set_if_present(sppm_section, "output_profile", "sppm_output_profile")

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


def _extract_sppm_preset_options(sppm_section: dict, profile_name: str) -> dict[str, object]:
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
