"""Load diagrams.toml defaults, select a preset, and validate effective options."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from flo.app._option_validation import validate_render_options
from flo.errors import EXIT_USAGE, CLIError

_TABLE = TypeAdapter(dict[str, Any])
_SPPM_FIELDS = {
    "max_width_px": "layout_max_width_px",
    "target_columns": "layout_target_columns",
    "wrap_layout": "layout_wrap",
    "spacing": "layout_spacing",
    "layout_spacing": "layout_spacing",
    "page_format": "publication_page_format",
    "label_density": "sppm_label_density",
    "text.wrap_strategy": "sppm_wrap_strategy",
    "text.truncation_policy": "sppm_truncation_policy",
    "text.max_label.step_name": "sppm_max_label_step_name",
    "text.max_label.workers": "sppm_max_label_workers",
    "text.max_label.ctwt": "sppm_max_label_ctwt",
}
_STYLE_FIELDS = {
    "theme": "theme",
    "background_color": "background_color",
    "font_family": "font_family",
    "typography_scale": "typography_scale",
    "canvas.background": "background_color",
    "typography.font_family": "font_family",
    "typography.scale": "typography_scale",
}


def merge_diagrams_toml_render_defaults(options: dict | None) -> dict:
    """Resolve CLI > selected preset > file defaults without injecting defaults."""
    opts = dict(options or {})
    config_file = _resolve_diagrams_toml_path(opts)
    if config_file is None:
        return validate_render_options(opts)
    try:
        data = tomllib.loads(config_file.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise CLIError(f"Failed to read diagrams.toml: {exc}", code=EXIT_USAGE) from exc
    try:
        defaults = _read_defaults(
            data,
            ("sppm",),
            {
                **_SPPM_FIELDS,
                "step_numbering": "sppm_step_numbering",
                "output_profile": "sppm_output_profile",
                "themes": "sppm_themes",
            },
        )
        defaults.update(_read_defaults(data, (), {"themes": "themes"}))
        for section in (("render",), ("render", "style")):
            defaults.update(_read_defaults(data, section, _STYLE_FIELDS))
        profile = (
            str(
                opts.get("sppm_output_profile")
                or defaults.get("sppm_output_profile", ("default", ""))[0]
                or "default"
            )
            .strip()
            .lower()
        )
        defaults_with_preset = {
            **defaults,
            **_read_defaults(
                data,
                ("sppm", "presets", profile),
                {"orientation": "orientation", **_SPPM_FIELDS},
            ),
        }
    except ValueError as exc:
        raise CLIError(
            f"Invalid diagrams.toml ({config_file}): {exc}. Correct this table and retry.",
            code=EXIT_USAGE,
            error_stage="option_validation",
        ) from exc
    resolved = {
        **{key: value for key, (value, _) in defaults_with_preset.items()},
        **opts,
    }
    config_keys = sorted(defaults.keys() - opts.keys())
    if config_keys:
        resolved["__diagrams_config_keys__"] = tuple(config_keys)
    origins = {
        key: path for key, (_, path) in defaults_with_preset.items() if key not in opts
    }
    return validate_render_options(resolved, config_file=config_file, origins=origins)


# Retained for callers using the former SPPM-only configuration entry point.
merge_diagrams_toml_sppm_defaults = merge_diagrams_toml_render_defaults


def _table_at(data: dict, path: tuple[str, ...]) -> dict:
    table = data
    for index, key in enumerate(path):
        if key not in table:
            return {}
        try:
            table = _TABLE.validate_python(table[key], strict=True)
        except ValidationError as exc:
            raise ValueError(f"{'.'.join(path[: index + 1])} must be a table") from exc
    return table


def _read_defaults(
    data: dict, section: tuple[str, ...], fields: dict[str, str]
) -> dict:
    """Map authored fields once, retaining their TOML paths for diagnostics."""
    result = {}
    for field, option in fields.items():
        path = (*section, *field.split("."))
        table = _table_at(data, path[:-1])
        if path[-1] in table:
            result[option] = (table[path[-1]], ".".join(path))
    return result


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
