"""Core package: application entrypoint and orchestrator.

This module is the package-level implementation previously provided by
`src/flo/core.py`. It exposes `run_content` and `run` as before.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

from flo.services.errors import EXIT_SUCCESS, ParseError, CompileError, ValidationError, RenderError

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir, IR
from flo.compiler.ir import ensure_schema_aligned
from flo.compiler.analysis import scc_condense
from flo.render import render_dot_and_contract, RenderOptions
from flo.export import export_ir
from flo.core._flo_config import merge_diagrams_toml_sppm_defaults
from flo.core._option_validation import validate_sppm_numeric_render_options, ensure_render_options_compatible_with_output

if TYPE_CHECKING:
    from flo.render._sppm_postprocess_contract import SppmSvgPostprocessContract


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
        ensure_render_options_compatible_with_output(options=options, output_format=output_format)
        return EXIT_SUCCESS, export_ir(ir, options={**(options or {}), "export": output_format}), ""

    resolved_options = merge_diagrams_toml_sppm_defaults(options=options)
    validate_sppm_numeric_render_options(options=resolved_options)
    render_to: str | None = (resolved_options or {}).get("render_to")
    render_options = RenderOptions.from_mapping(resolved_options)

    dot, contract = _render_dot_with_postprocess(ir, render_options=render_options)
    if render_to:
        from flo.services.graphviz import render_dot_to_file
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


def _render_dot_with_postprocess(ir: IR, render_options: RenderOptions) -> tuple[str, SppmSvgPostprocessContract | None]:
    """SCC-condense then render, returning (dot, sppm_contract)."""
    processed = ir

    try:
        processed = scc_condense(processed)
    except Exception:
        pass

    try:
        dot, contract = render_dot_and_contract(processed, options=render_options)
    except Exception as e:
        raise RenderError(str(e))

    return dot, contract


def run() -> Tuple[int, str, str]:
    """Programmatic entrypoint that runs an empty input (used in tests)."""
    return run_content("")
