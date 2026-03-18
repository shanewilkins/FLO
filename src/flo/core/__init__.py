"""Core package: application entrypoint and orchestrator.

This module is the package-level implementation previously provided by
`src/flo/core.py`. It exposes `run_content` and `run` as before.
"""
from __future__ import annotations

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

    return EXIT_SUCCESS, _render_dot_with_postprocess(ir, options=options), ""


def _parse_compile_validate(content: str, source_path: str | None = None) -> IR:
    try:
        try:
            adapter_model = parse_adapter(content, source_path=source_path)
        except TypeError:
            adapter_model = parse_adapter(content)
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
        )
        if flag in opts
    ]
    if invalid:
        names = ", ".join(f"--{name}" for name in invalid)
        raise CLIError(
            f"Render options {names} require DOT output. Use --export dot or remove those flags.",
            code=EXIT_USAGE,
        )


def _render_dot_with_postprocess(ir: IR, options: dict | None = None) -> str:
    processed = ir

    try:
        processed = scc_condense(processed)
    except Exception:
        pass

    try:
        try:
            _dot = render_dot(processed, options=options)
        except TypeError:
            _dot = render_dot(processed)
    except Exception as e:
        raise RenderError(str(e))

    return _dot


def run() -> Tuple[int, str, str]:
    """Programmatic entrypoint that runs an empty input (used in tests)."""
    return run_content("")
