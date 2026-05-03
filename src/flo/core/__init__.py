"""Core package: application entrypoint and orchestrator.

This module is the package-level implementation previously provided by
`src/flo/core.py`. It exposes `run_content` and `run` as before.
"""
from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Tuple

from flo.services.errors import EXIT_SUCCESS, ParseError, CompileError, ValidationError, RenderError
from flo.services.errors import CLIError, EXIT_USAGE

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir, IR
from flo.compiler.ir import ensure_schema_aligned
from flo.compiler.analysis import scc_condense
from flo.render import render_dot
from flo.export import export_ir


def run_content(content: str, command: str = "run", options: dict | None = None) -> Tuple[int, str, str]:
    """Run the content through parse -> compile -> validate -> render.

    Returns a tuple of (exit_code, output, error_message).
    """
    if not content:
        return EXIT_SUCCESS, "", ""

    source_path = (options or {}).get("source_path") if isinstance(options, dict) else None
    ir = _parse_compile_validate(content, source_path=source_path)

    if command == "validate":
        return EXIT_SUCCESS, "", ""

    output_format = _resolve_output_format(command=command, options=options)
    if output_format in {"json", "ingredients", "movement"}:
        _ensure_render_options_compatible_with_output(options=options, output_format=output_format)
        return EXIT_SUCCESS, export_ir(ir, options={**(options or {}), "export": output_format}), ""

    resolved_options = _merge_diagrams_toml_sppm_defaults(options=options)
    _validate_sppm_numeric_render_options(options=resolved_options)

    dot = _render_dot_with_postprocess(ir, options=resolved_options)
    render_to = (resolved_options or {}).get("render_to")
    if render_to:
        from flo.render import get_last_sppm_contract
        from flo.services.graphviz import render_dot_to_file
        
        contract = get_last_sppm_contract()
        render_dot_to_file(dot, render_to, sppm_contract=contract)
        return EXIT_SUCCESS, "", ""
    return EXIT_SUCCESS, dot, ""


def _parse_compile_validate(content: str, source_path: str | None = None) -> IR:
    try:
        adapter_model = parse_adapter(content, source_path=source_path)
    except Exception as e:
        raise ParseError(str(e))

    try:
        ir = compile_adapter(adapter_model)
    except Exception as e:
        raise CompileError(str(e))

    try:
        validate_ir(ir)
    except Exception as e:
        raise ValidationError(str(e))

    if isinstance(ir, IR):
        try:
            ensure_schema_aligned(ir)
        except Exception as e:
            raise ValidationError(str(e))

    return ir


def _resolve_output_format(command: str, options: dict | None) -> str:
    output_format = (options or {}).get("export") or (options or {}).get("format")
    if command == "compile":
        return "json"
    if command in {"run", "export"} and output_format in {"json", "ingredients", "movement"}:
        return str(output_format)
    return "dot"


def _ensure_render_options_compatible_with_output(options: dict | None, output_format: str) -> None:
    if output_format == "dot":
        return

    opts = options or {}
    invalid = [
        flag
        for flag in (
            "diagram",
            "profile",
            "detail",
            "orientation",
            "show_notes",
            "subprocess_view",
            "spaghetti_channel",
            "spaghetti_people_mode",
            "sppm_theme",
            "layout_wrap",
            "layout_fit",
            "layout_spacing",
            "sppm_step_numbering",
            "sppm_label_density",
            "sppm_wrap_strategy",
            "sppm_truncation_policy",
            "layout_max_width_px",
            "layout_target_columns",
            "sppm_max_label_step_name",
            "sppm_max_label_workers",
            "sppm_max_label_ctwt",
            "sppm_output_profile",
            "render_to",
        )
        if flag in opts
    ]
    if invalid:
        names = ", ".join(f"--{name}" for name in invalid)
        raise CLIError(
            f"Render options {names} require DOT output. Use --export dot or remove those flags.",
            code=EXIT_USAGE,
        )


def _validate_sppm_numeric_render_options(options: dict | None) -> None:
    opts = options or {}
    numeric_flags = (
        "layout_max_width_px",
        "layout_target_columns",
        "sppm_max_label_step_name",
        "sppm_max_label_workers",
        "sppm_max_label_ctwt",
    )

    for flag in numeric_flags:
        if flag not in opts:
            continue
        raw_value = opts.get(flag)
        if raw_value is None:
            parsed = 0
            if parsed <= 0:
                cli_flag = f"--{flag.replace('_', '-')}"
                raise CLIError(
                    f"Invalid value for {cli_flag}: expected a positive integer.",
                    code=EXIT_USAGE,
                )
            continue
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError):
            parsed = 0

        if parsed <= 0:
            cli_flag = f"--{flag.replace('_', '-')}"
            raise CLIError(
                f"Invalid value for {cli_flag}: expected a positive integer.",
                code=EXIT_USAGE,
            )


def _merge_diagrams_toml_sppm_defaults(options: dict | None) -> dict:
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


def _render_dot_with_postprocess(ir: IR, options: dict | None = None) -> str:
    processed = ir

    try:
        processed = scc_condense(processed)
    except Exception:
        pass

    try:
        _dot = render_dot(processed, options=options)
    except Exception as e:
        raise RenderError(str(e))

    return _dot


def run() -> Tuple[int, str, str]:
    """Programmatic entrypoint that runs an empty input (used in tests)."""
    return run_content("")
