"""Core package: application entrypoint and orchestrator.

This package is the composition root for CLI and programmatic application use.
It exposes `run_content` and `run`.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from flo.app._capability_validation import ensure_render_projection_supported
from flo.app._flo_config import merge_diagrams_toml_render_defaults
from flo.app._option_validation import (
    ensure_render_options_compatible_with_output,
    validate_sppm_numeric_render_options,
)
from flo.app.inspect import (
    format_model_inspection,
    format_structural_analysis,
    format_timing_analysis,
)
from flo.app.io import write_output
from flo.app.render_intent import RenderIntentResolver
from flo.app.runtime_services import Services as Services
from flo.app.runtime_services import get_services as get_services
from flo.errors import (
    EXIT_SUCCESS,
    EXIT_USAGE,
    CLIError,
    CompileError,
    ParseError,
    RenderError,
    ValidationError,
)
from flo.process.analysis import (
    analyze_process_structure,
    analyze_process_timing,
    inspect_process_model,
)
from flo.process.export import export_ir
from flo.process.ir import IR, ensure_schema_aligned, validate_ir
from flo.render import RenderArtifact, RenderOptions, render_artifact_and_contract
from flo.render.capability_matrix import RENDER_CAPABILITY_MATRIX
from flo.render.sppm.publication_artifact import (
    render_sppm_typst_publication_artifact,
)
from flo.render.themes import ThemeValidationError
from flo.source import (
    SourceComposition,
    compile_adapter,
    parse_adapter,
    pop_source_composition,
)


def run_content(
    content: str, command: str = "render", options: dict | None = None
) -> tuple[int, str, str]:
    """Run the content through parse -> compile -> validate -> render.

    Returns a tuple of (exit_code, output, error_message).
    """
    source_path = _resolve_source_path(options)
    ir, composition = _parse_compile_validate(content, source_path=source_path)

    if command == "validate":
        return EXIT_SUCCESS, "", ""

    if command == "inspect":
        return _run_inspect_output(ir=ir, options=options, composition=composition)

    output_format = _resolve_output_format(command=command, options=options)
    if output_format in {"json", "ingredients", "movement"}:
        return _run_export_output(ir=ir, options=options, output_format=output_format)
    if output_format == "typst":
        return _run_typst_publication_output(ir=ir, options=options)

    return _run_render_output(ir=ir, options=options, output_format=output_format)


def _run_inspect_output(
    *,
    ir: IR,
    options: dict | None,
    composition: SourceComposition,
) -> tuple[int, str, str]:
    analysis, output_format, for_analysis, for_diagram = _resolve_inspect_request(
        options
    )
    if analysis == "model":
        report = inspect_process_model(
            ir,
            entry_source=composition.entry_source,
            included_sources=composition.included_sources,
            requested_analysis=for_analysis,
            requested_diagram=for_diagram,
            supported_diagrams=_supported_svg_diagrams(),
        )
        return (
            EXIT_SUCCESS,
            format_model_inspection(report, output_format=output_format),
            "",
        )

    if analysis == "structure":
        structural_result = analyze_process_structure(ir)
        return (
            EXIT_SUCCESS,
            format_structural_analysis(structural_result, output_format=output_format),
            "",
        )

    result = analyze_process_timing(ir)
    return (
        EXIT_SUCCESS,
        format_timing_analysis(result, output_format=output_format),
        "",
    )


def _resolve_inspect_request(
    options: dict | None,
) -> tuple[str, str, str | None, str | None]:
    analysis = str((options or {}).get("analysis", "timing"))
    output_format = str((options or {}).get("format", "text"))
    if analysis not in {"timing", "structure", "model"}:
        raise CLIError(
            f"Unsupported inspect analysis: {analysis}",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )
    if output_format not in {"text", "json"}:
        raise CLIError(
            f"Unsupported inspect format: {output_format}",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )

    raw_for_analysis = (options or {}).get("for_analysis")
    raw_for_diagram = (options or {}).get("for_diagram")
    for_analysis = str(raw_for_analysis) if raw_for_analysis is not None else None
    for_diagram = str(raw_for_diagram) if raw_for_diagram is not None else None
    if analysis != "model" and (for_analysis or for_diagram):
        raise CLIError(
            "--for-analysis and --for-diagram require --analysis model",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )
    if for_analysis not in {None, "timing", "structure"}:
        raise CLIError(
            f"Unsupported readiness analysis: {for_analysis}",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )
    if for_diagram not in {
        None,
        "sppm",
        "swimlane",
        "spaghetti",
        "value_stream",
    }:
        raise CLIError(
            f"Unsupported readiness diagram: {for_diagram}",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )
    return analysis, output_format, for_analysis, for_diagram


def _resolve_source_path(options: dict | None) -> str | None:
    if not isinstance(options, dict):
        return None
    source_path = options.get("source_path")
    return source_path if isinstance(source_path, str) else None


def _run_export_output(
    *,
    ir: IR,
    options: dict | None,
    output_format: str,
) -> tuple[int, str, str]:
    try:
        ensure_render_options_compatible_with_output(
            options=options,
            output_format=output_format,
        )
    except CLIError as exc:
        _raise_with_stage(exc, stage="option_validation")

    try:
        exported = export_ir(
            ir,
            options={**(options or {}), "export": output_format},
        )
    except CLIError as exc:
        _raise_with_stage(exc, stage="export_generate")
    except Exception as exc:
        raise RenderError(str(exc), error_stage="export_generate") from exc

    return (EXIT_SUCCESS, exported, "")


def _run_render_output(
    *,
    ir: IR,
    options: dict | None,
    output_format: str,
) -> tuple[int, str, str]:
    resolved_options = merge_diagrams_toml_render_defaults(options=options)
    validate_sppm_numeric_render_options(options=resolved_options)
    render_to: str | None = (resolved_options or {}).get("render_to")

    resolved_options = _merge_render_intent_options(ir=ir, options=resolved_options)
    render_options = _resolve_render_options_for_output(
        resolved_options=resolved_options,
        output_format=output_format,
    )
    ensure_render_projection_supported(render_options)

    artifact, contract, warning = _render_artifact_with_diagnostics(
        ir,
        render_options=render_options,
    )
    if render_to:
        _write_render_artifact(
            artifact=artifact,
            render_to=render_to,
            contract=contract,
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


def _run_typst_publication_output(
    *, ir: IR, options: dict | None
) -> tuple[int, str, str]:
    resolved_options = merge_diagrams_toml_render_defaults(options=options)
    validate_sppm_numeric_render_options(options=resolved_options)
    resolved_options = _merge_render_intent_options(ir=ir, options=resolved_options)
    render_options = RenderOptions.from_mapping(resolved_options)
    if render_options.diagram != "sppm":
        raise CLIError(
            "Typst publication output is currently supported only for --diagram sppm.",
            code=EXIT_USAGE,
            error_stage="option_validation",
        )
    artifact = render_sppm_typst_publication_artifact(ir, render_options)
    render_to = (resolved_options or {}).get("render_to")
    if isinstance(render_to, str) and render_to:
        _write_render_artifact(artifact=artifact, render_to=render_to, contract=None)
        return EXIT_SUCCESS, "", ""
    return EXIT_SUCCESS, artifact.content, ""


def _merge_render_intent_options(*, ir: IR, options: dict | None) -> dict | None:
    # Extract view-aware render intent from compiled IR (wires resolver into pipeline)
    return _merge_view_intent_options(
        render_metadata=ir.render_intent,
        options=options,
    )


def _parse_compile_validate(
    content: str, source_path: str | None = None
) -> tuple[IR, SourceComposition]:
    from flo.source.diagnostics import source_diagnostic

    try:
        adapter_model = parse_adapter(content, source_path=source_path)
    except Exception as exc:
        diagnostic = source_diagnostic(
            str(exc),
            content=content,
            source_path=source_path,
            cause=exc,
        )
        error = ParseError(diagnostic.render(), error_stage="parse")
        error.diagnostic = diagnostic
        raise error from exc

    composition = (
        pop_source_composition(adapter_model, source_path=source_path)
        if isinstance(adapter_model, dict)
        else SourceComposition(
            entry_source="<stdin>" if source_path == "-" else "<memory>"
        )
    )
    try:
        ir = compile_adapter(adapter_model)
    except Exception as exc:
        diagnostic = source_diagnostic(
            str(exc), content=content, source_path=source_path, cause=exc
        )
        error = CompileError(diagnostic.render(), error_stage="compile")
        error.diagnostic = diagnostic
        raise error from exc

    try:
        validate_ir(ir)
    except ValidationError as exc:
        error_stage = getattr(exc, "error_stage", None) or "validate"
        diagnostic = source_diagnostic(
            str(exc),
            content=content,
            source_path=source_path,
            cause=exc,
        )
        error = ValidationError(diagnostic.render(), error_stage=error_stage)
        error.diagnostic = diagnostic
        raise error from exc
    except Exception as exc:
        diagnostic = source_diagnostic(
            str(exc), content=content, source_path=source_path, cause=exc
        )
        error = ValidationError(diagnostic.render(), error_stage="validate")
        error.diagnostic = diagnostic
        raise error from exc

    if isinstance(ir, IR):
        try:
            ensure_schema_aligned(ir)
        except ValidationError as exc:
            error_stage = getattr(exc, "error_stage", None) or "schema_validate"
            diagnostic = source_diagnostic(
                str(exc), content=content, source_path=source_path, cause=exc
            )
            error = ValidationError(diagnostic.render(), error_stage=error_stage)
            error.diagnostic = diagnostic
            raise error from exc
        except Exception as exc:
            diagnostic = source_diagnostic(
                str(exc), content=content, source_path=source_path, cause=exc
            )
            error = ValidationError(diagnostic.render(), error_stage="schema_validate")
            error.diagnostic = diagnostic
            raise error from exc

    return ir, composition


def _supported_svg_diagrams() -> tuple[str, ...]:
    return tuple(
        sorted(
            diagram
            for diagram, backends in RENDER_CAPABILITY_MATRIX.items()
            if bool((backends.get("svg") or {}).get("supported"))
        )
    )


def _raise_with_stage(exc: CLIError, *, stage: str) -> None:
    if getattr(exc, "error_stage", None) is None:
        exc.error_stage = stage
    raise exc


def _resolve_output_format(command: str, options: dict | None) -> str:
    output_format = (options or {}).get("export") or (options or {}).get("format")
    if command in {"render", "export"} and output_format in {
        "json",
        "ingredients",
        "movement",
        "svg",
        "typst",
    }:
        return str(output_format)
    render_to = (options or {}).get("render_to")
    if (
        output_format is None
        and isinstance(render_to, str)
        and Path(render_to).suffix.lower() == ".svg"
    ):
        return "svg"
    return "svg"


def _resolve_render_options_for_output(
    *, resolved_options: dict | None, output_format: str
) -> RenderOptions:
    try:
        render_options = RenderOptions.from_mapping(resolved_options)
    except ThemeValidationError as exc:
        raise CLIError(
            str(exc), code=EXIT_USAGE, error_stage="option_validation"
        ) from exc
    explicit_backend = (resolved_options or {}).get("render_backend")

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

    config_keys = set(merged.pop("__diagrams_config_keys__", ()) or ())
    cli_overrides = {
        key: value for key, value in merged.items() if key not in config_keys
    }
    profile_raw = merged.get("profile")
    profile = str(profile_raw).strip().lower() if profile_raw is not None else "default"
    view_raw = merged.get("view")
    view_name = str(view_raw).strip() if view_raw is not None else "default"

    resolved_intent = RenderIntentResolver.resolve(
        render_metadata=render_metadata,
        cli_overrides=cli_overrides,
        profile=profile or "default",
        view_name=view_name or "default",
    )
    baseline_intent = RenderIntentResolver.resolve(
        render_metadata=None,
        cli_overrides=cli_overrides,
        profile=profile or "default",
        view_name=view_name or "default",
    )

    intent_overrides = _render_intent_overrides(
        resolved_intent=resolved_intent,
        baseline_intent=baseline_intent,
    )
    merged.update(intent_overrides)
    merged.update(cli_overrides)
    if "sppm_theme" in cli_overrides and "theme" not in cli_overrides:
        merged["theme"] = cli_overrides["sppm_theme"]
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
        ("layout_width", "layout_width"),
        ("layout_height", "layout_height"),
        ("layout_overflow", "layout_overflow"),
        ("sppm_label_density", "sppm_label_density"),
        ("sppm_node_numbering", "sppm_step_numbering"),
        ("spaghetti_channel", "spaghetti_channel"),
        ("spaghetti_people_mode", "spaghetti_people_mode"),
        ("spaghetti_strict_spatial", "spaghetti_strict_spatial"),
        ("theme", "theme"),
        ("background_color", "background_color"),
        ("font_family", "font_family"),
        ("typography_scale", "typography_scale"),
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


def _render_artifact_with_diagnostics(
    ir: IR, render_options: RenderOptions
) -> tuple[RenderArtifact, None, str | None]:
    """Render untouched canonical IR and return any artifact-owned warning."""
    try:
        artifact, contract = render_artifact_and_contract(ir, options=render_options)
    except Exception as exc:
        raise RenderError(str(exc)) from exc

    warning: str | None = None
    artifact_warning = artifact.metadata.get("warning")
    if isinstance(artifact_warning, str) and artifact_warning.strip():
        warning = "\n".join(
            item for item in (warning, artifact_warning.strip()) if item
        )
    return artifact, contract, warning


def _write_render_artifact(
    *,
    artifact: RenderArtifact,
    render_to: str,
    contract: None,
) -> None:
    kind = artifact.kind
    content = artifact.content
    if kind == "svg":
        if Path(render_to).suffix.lower() != ".svg":
            raise RenderError(
                "Direct SVG rendering currently supports only .svg output paths. "
                "Use a .svg target for rendered diagram output."
            )
        write_rc, write_err = write_output(content, render_to)
        if write_rc != 0:
            raise RenderError(write_err)
        return
    if kind == "typst":
        if Path(render_to).suffix.lower() != ".typ":
            raise RenderError("Typst publication output requires a .typ output path.")
        _write_typst_publication_assets(artifact=artifact, render_to=render_to)
        write_rc, write_err = write_output(content, render_to)
        if write_rc != 0:
            raise RenderError(write_err)
        return
    raise RenderError(f"Unsupported render artifact kind: {kind or 'unknown'}")


def _write_typst_publication_assets(
    *, artifact: RenderArtifact, render_to: str
) -> None:
    assets = artifact.metadata.get("page_svg_assets", ())
    if not isinstance(assets, tuple):
        return
    output_directory = Path(render_to).parent
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_path = asset.get("asset_path")
        content = asset.get("content")
        if not isinstance(asset_path, str) or not isinstance(content, str):
            continue
        relative_path = Path(asset_path)
        if relative_path.name != asset_path:
            raise RenderError("Typst publication SVG asset paths must be file names.")
        write_rc, write_err = write_output(
            content, str(output_directory / relative_path)
        )
        if write_rc != 0:
            raise RenderError(write_err)


def _render_artifact_for_stdout(
    *,
    artifact: RenderArtifact,
    output_format: str,
    contract: None,
) -> str:
    """Materialize the requested stdout format from a backend-neutral artifact."""
    if artifact.kind == "svg":
        return artifact.content
    if artifact.kind == "typst" and output_format == "typst":
        return artifact.content
    raise RenderError(f"Unsupported render artifact kind: {artifact.kind or 'unknown'}")


def run() -> tuple[int, str, str]:
    """Return the no-input programmatic placeholder result."""
    return EXIT_SUCCESS, "", ""
