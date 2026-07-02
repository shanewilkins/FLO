"""Core package: application entrypoint and orchestrator.

This module is the package-level implementation previously provided by
`src/flo/core.py`. It exposes `run_content` and `run` as before.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Tuple

from flo.services.errors import (
    CLIError,
    EXIT_SUCCESS,
    EXIT_USAGE,
    ParseError,
    CompileError,
    ValidationError,
    RenderError,
)

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir, IR
from flo.compiler.ir import ensure_schema_aligned
from flo.compiler.analysis import scc_condense
from flo.render import RenderArtifact, render_artifact_and_contract, RenderOptions
from flo.export import export_ir
from flo.core._flo_config import merge_diagrams_toml_sppm_defaults
from flo.core._option_validation import (
    validate_sppm_numeric_render_options,
    ensure_render_options_compatible_with_output,
)
from flo.core._capability_validation import ensure_render_projection_supported
from flo.core.render_intent import RenderIntentResolver
from flo.services.io import write_output

if TYPE_CHECKING:
    from flo.render._sppm_postprocess_contract import SppmSvgPostprocessContract


_FAIL_OPEN_SCC_PREFIX = "fail-open postprocess: scc_condense failed"


def run_content(
    content: str, command: str = "run", options: dict | None = None
) -> Tuple[int, str, str]:
    """Run the content through parse -> compile -> validate -> render.

    Returns a tuple of (exit_code, output, error_message).
    """
    if not content:
        return EXIT_SUCCESS, "", ""

    source_path = (
        (options or {}).get("source_path") if isinstance(options, dict) else None
    )
    ir = _parse_compile_validate(content, source_path=source_path)

    if command == "validate":
        return EXIT_SUCCESS, "", ""

    output_format = _resolve_output_format(command=command, options=options)
    if output_format in {"json", "ingredients", "movement"}:
        ensure_render_options_compatible_with_output(
            options=options, output_format=output_format
        )
        return (
            EXIT_SUCCESS,
            export_ir(ir, options={**(options or {}), "export": output_format}),
            "",
        )

    resolved_options = merge_diagrams_toml_sppm_defaults(options=options)
    validate_sppm_numeric_render_options(options=resolved_options)
    render_to: str | None = (resolved_options or {}).get("render_to")

    # Extract view-aware render intent from compiled IR (wires resolver into pipeline)
    render_metadata = None
    if isinstance(ir, IR) and isinstance(ir.process_metadata, dict):
        render_metadata = ir.process_metadata.get("render")
    resolved_options = _merge_view_intent_options(
        render_metadata=render_metadata,
        options=resolved_options,
    )

    render_options = _resolve_render_options_for_output(
        resolved_options=resolved_options,
        output_format=output_format,
    )
    ensure_render_projection_supported(render_options)

    artifact, contract, warning = _render_artifact_with_postprocess(
        ir, render_options=render_options
    )
    if render_to:
        _write_render_artifact(
            artifact=artifact, render_to=render_to, contract=contract
        )
        return EXIT_SUCCESS, "", warning or ""
    return (
        EXIT_SUCCESS,
        _render_artifact_for_stdout(
            artifact=artifact,
            output_format=output_format,
            contract=contract,
        ),
        warning or "",
    )


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
    if command in {"run", "export"} and output_format in {
        "json",
        "ingredients",
        "movement",
        "svg",
    }:
        return str(output_format)
    render_to = (options or {}).get("render_to")
    if output_format is None and isinstance(render_to, str):
        if Path(render_to).suffix.lower() == ".svg":
            return "svg"
    return "dot"


def _resolve_render_options_for_output(
    *, resolved_options: dict | None, output_format: str
) -> RenderOptions:
    render_options = RenderOptions.from_mapping(resolved_options)
    explicit_backend = (resolved_options or {}).get("render_backend")

    if output_format == "dot":
        if explicit_backend not in {None, "", "graphviz"}:
            raise CLIError(
                "DOT export is deprecated compatibility-only and currently requires --render-backend graphviz or no --render-backend.",
                code=EXIT_USAGE,
            )
        return replace(render_options, backend="graphviz")

    if output_format == "svg":
        if explicit_backend not in {None, "", "svg"}:
            raise CLIError(
                "SVG export currently requires --render-backend svg or no --render-backend.",
                code=EXIT_USAGE,
            )
        return replace(render_options, backend="svg")

    return render_options


def _merge_view_intent_options(
    *, render_metadata: Any, options: dict | None
) -> dict[str, Any]:
    """Merge source render intent into CLI options without changing legacy defaults.

    We only apply values introduced by source render metadata. Resolver profile/hard
    defaults are intentionally ignored here so no-metadata behavior remains
    compatible with existing RenderOptions defaults.
    """
    merged: dict[str, Any] = dict(options or {})
    if not isinstance(render_metadata, dict):
        return merged

    profile_raw = merged.get("profile")
    profile = str(profile_raw).strip().lower() if profile_raw is not None else "default"
    view_raw = merged.get("view")
    view_name = str(view_raw).strip() if view_raw is not None else "default"

    resolved_intent = RenderIntentResolver.resolve(
        render_metadata=render_metadata,
        cli_overrides=merged,
        profile=profile or "default",
        view_name=view_name or "default",
    )
    baseline_intent = RenderIntentResolver.resolve(
        render_metadata=None,
        cli_overrides=merged,
        profile=profile or "default",
        view_name=view_name or "default",
    )

    intent_overrides = _render_intent_overrides(
        resolved_intent=resolved_intent,
        baseline_intent=baseline_intent,
    )
    merged.update(intent_overrides)
    return merged


def _render_intent_overrides(
    *,
    resolved_intent: Any,
    baseline_intent: Any,
) -> dict[str, Any]:
    """Translate metadata-contributed intent deltas into RenderOptions input keys."""

    def changed(field: str) -> bool:
        return getattr(resolved_intent, field) != getattr(baseline_intent, field)

    overrides: dict[str, Any] = {}
    _collect_changed_value_overrides(
        overrides=overrides,
        resolved_intent=resolved_intent,
        changed=changed,
    )
    _collect_changed_inverted_boolean_overrides(
        overrides=overrides,
        resolved_intent=resolved_intent,
        changed=changed,
    )
    return overrides


def _collect_changed_value_overrides(
    *,
    overrides: dict[str, Any],
    resolved_intent: Any,
    changed: Any,
) -> None:
    mappings = (
        ("diagram", "diagram"),
        ("publication_page_format", "publication_page_format"),
        ("layout_wrap", "layout_wrap"),
        ("layout_max_width", "layout_max_width_px"),
        ("layout_target_columns", "layout_target_columns"),
        ("sppm_label_density", "sppm_label_density"),
        ("sppm_node_numbering", "sppm_step_numbering"),
        ("spaghetti_channel", "spaghetti_channel"),
        ("spaghetti_people_mode", "spaghetti_people_mode"),
    )
    for intent_field, option_field in mappings:
        value = getattr(resolved_intent, intent_field)
        if changed(intent_field) and value is not None:
            overrides[option_field] = value


def _collect_changed_inverted_boolean_overrides(
    *,
    overrides: dict[str, Any],
    resolved_intent: Any,
    changed: Any,
) -> None:
    mappings = (
        ("publication_header_enabled", "sppm_no_header"),
        ("publication_footer_enabled", "sppm_no_footer"),
    )
    for intent_field, option_field in mappings:
        value = getattr(resolved_intent, intent_field)
        if changed(intent_field) and value is not None:
            overrides[option_field] = not bool(value)


def render_dot_and_contract(
    ir: IR, options: RenderOptions | dict | None = None
) -> tuple[str, SppmSvgPostprocessContract | None]:
    """Legacy compatibility wrapper for callers still expecting DOT plus contract."""
    artifact, contract = render_artifact_and_contract(ir, options=options)
    return artifact.content, contract


def _render_artifact_with_postprocess(
    ir: IR, render_options: RenderOptions
) -> tuple[RenderArtifact, SppmSvgPostprocessContract | None, str | None]:
    """SCC-condense then render, returning (artifact, backend contract)."""
    processed = ir
    warning: str | None = None

    try:
        processed = scc_condense(processed)
    except Exception as exc:
        # Explicit fail-open policy: when SCC postprocess fails, continue with
        # original IR and surface a deterministic warning for diagnostics.
        warning = f"{_FAIL_OPEN_SCC_PREFIX}: {exc}"

    try:
        artifact, contract = render_artifact_and_contract(
            processed, options=render_options
        )
    except Exception as e:
        raise RenderError(str(e))

    return artifact, contract, warning


def _write_render_artifact(
    *,
    artifact: RenderArtifact,
    render_to: str,
    contract: SppmSvgPostprocessContract | None,
) -> None:
    kind = artifact.kind
    content = artifact.content
    if kind == "dot":
        from flo.services.graphviz import render_dot_to_file

        render_dot_to_file(content, render_to, sppm_contract=contract)
        return
    if kind == "svg":
        if Path(render_to).suffix.lower() != ".svg":
            raise RenderError(
                "Direct SVG rendering currently supports only .svg output paths. "
                "Use a .svg target or switch to the deprecated Graphviz backend for raster/PDF output."
            )
        write_rc, write_err = write_output(content, render_to)
        if write_rc != 0:
            raise RenderError(write_err)
        return
    raise RenderError(f"Unsupported render artifact kind: {kind or 'unknown'}")


def _render_artifact_for_stdout(
    *,
    artifact: RenderArtifact,
    output_format: str,
    contract: SppmSvgPostprocessContract | None,
) -> str:
    """Materialize the requested stdout format from a backend-neutral artifact."""
    if artifact.kind == "svg" or output_format != "svg":
        return artifact.content
    if artifact.kind != "dot":
        raise RenderError(
            f"Unsupported render artifact kind: {artifact.kind or 'unknown'}"
        )

    from flo.services.graphviz import render_dot_to_file

    with TemporaryDirectory(prefix="flo-svg-stdout-") as temp_dir:
        svg_path = Path(temp_dir) / "stdout.svg"
        render_dot_to_file(artifact.content, str(svg_path), sppm_contract=contract)
        return svg_path.read_text(encoding="utf-8")


def run() -> Tuple[int, str, str]:
    """Programmatic entrypoint that runs an empty input (used in tests)."""
    return run_content("")
