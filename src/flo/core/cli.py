"""CLI entry points for the FLO tool."""

from __future__ import annotations

import sys
import uuid
from typing import Any, Optional

import click
from flo.core.render_option_schema import iter_render_option_specs
from structlog.contextvars import bind_contextvars, unbind_contextvars


# ---------------------------------------------------------------------------
# Shared execution helper (used by both Click handlers and console_main)
# ---------------------------------------------------------------------------


def _emit_error(services: Any, message: str, **event_fields: object) -> None:
    """Emit a user-facing error message plus structured context fields.

    The message contract remains unchanged (stderr), while event fields are
    attached through structlog contextvars for observability backends.
    """
    bound_keys = tuple(key for key, value in event_fields.items() if value is not None)
    try:
        bind_contextvars(**{key: event_fields[key] for key in bound_keys})
    except Exception:
        bound_keys = tuple()

    try:
        services.error_handler(message)
    finally:
        if bound_keys:
            try:
                unbind_contextvars(*bound_keys)
            except Exception:
                pass


def _get_flo_version() -> str:  # pragma: no cover - importlib optional
    """Return the installed FLO version or 'unknown' when not resolvable."""
    try:
        import importlib.metadata as _meta

        return _meta.version("flo")
    except Exception:
        return "unknown"


def _safe_set_span_attr(span: Any, key: str, value: object) -> None:
    setter = getattr(span, "set_attribute", None)
    if callable(setter):
        try:
            setter(key, value)
        except Exception:
            pass


def _safe_add_span_event(
    span: Any, event_name: str, attributes: dict[str, object]
) -> None:
    add_event = getattr(span, "add_event", None)
    if callable(add_event):
        try:
            add_event(event_name, attributes)
        except Exception:
            pass


def _handle_run_content_exception(
    *,
    root_span: Any,
    exc: Exception,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> int:
    from flo.services.errors import map_exception_to_rc
    from flo.services.telemetry import record_span_error

    mapped_rc, msg, internal = map_exception_to_rc(exc)
    _safe_set_span_attr(root_span, "flo.exit_code", mapped_rc)
    record_span_error(root_span, msg or "")
    display_msg = f"Unexpected error: {msg or 'internal error'}" if internal else msg
    _emit_error(
        services,
        display_msg,
        error_kind="internal" if internal else "domain",
        error_stage="run_content",
        exit_code=mapped_rc,
        internal=internal,
        command=command,
        command_id=command_id,
        path=effective_path,
    )
    return mapped_rc


def _handle_nonzero_run_content_result(
    *,
    root_span: Any,
    rc: int,
    err: str | None,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> int:
    from flo.services.telemetry import record_span_error

    _safe_set_span_attr(root_span, "flo.exit_code", rc)
    record_span_error(root_span, err or f"command failed with exit code {rc}")
    if err:
        _emit_error(
            services,
            err,
            error_kind="domain",
            error_stage="run_content",
            exit_code=rc,
            internal=False,
            command=command,
            command_id=command_id,
            path=effective_path,
        )
    return rc


def _handle_degraded_success(
    *,
    root_span: Any,
    err: str | None,
    options: dict,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> None:
    if not err:
        return
    _safe_set_span_attr(root_span, "flo.degraded", True)
    _safe_set_span_attr(root_span, "flo.degraded_reason", err)
    _safe_add_span_event(root_span, "flo.degraded", {"flo.degraded_reason": err})
    if options.get("verbose"):
        _emit_error(
            services,
            f"Warning: {err}",
            error_kind="diagnostic",
            error_stage="fail_open_fallback",
            exit_code=0,
            internal=False,
            command=command,
            command_id=command_id,
            path=effective_path,
        )


def _write_output_or_emit_failure(
    *,
    root_span: Any,
    out: str | None,
    options: dict,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> int | None:
    from flo.services.io import write_output
    from flo.services.telemetry import record_span_error

    if not out:
        return None
    _safe_set_span_attr(root_span, "flo.output.bytes", len(out))
    _safe_set_span_attr(root_span, "flo.output.to_file", bool(options.get("output")))
    write_rc, write_err = write_output(out, options.get("output"))
    if write_rc == 0:
        return None
    _safe_set_span_attr(root_span, "flo.exit_code", write_rc)
    record_span_error(root_span, write_err or "")
    _emit_error(
        services,
        write_err,
        error_kind="io",
        error_stage="write_output",
        exit_code=write_rc,
        internal=False,
        command=command,
        command_id=command_id,
        path=effective_path,
    )
    return write_rc


def _execute_span_body(
    root_span: Any,
    path: str | None,
    command: str,
    options: dict,
    services: Any,
    command_id: str,
) -> int:
    """Run the FLO pipeline within an existing trace span.

    Returns an integer exit code.
    """
    from flo.core import run_content
    from flo.services.io import read_input
    from flo.services.telemetry import record_span_error

    effective_path = path or "-"
    _safe_set_span_attr(root_span, "flo.command", command)
    _safe_set_span_attr(root_span, "flo.command_id", command_id)
    _safe_set_span_attr(root_span, "flo.input.path", effective_path)
    _safe_set_span_attr(root_span, "flo.input.from_stdin", effective_path == "-")
    rc, content, err = read_input(effective_path)
    if rc != 0:
        _safe_set_span_attr(root_span, "flo.exit_code", rc)
        record_span_error(root_span, err or "")
        _emit_error(
            services,
            err,
            error_kind="io",
            error_stage="read_input",
            exit_code=rc,
            internal=False,
            command=command,
            command_id=command_id,
            path=effective_path,
        )
        return rc
    _safe_set_span_attr(root_span, "flo.input.bytes", len(content or ""))

    run_options = dict(options)
    if path and path != "-":
        run_options.setdefault("source_path", path)
    _safe_set_span_attr(root_span, "flo.options.count", len(run_options))

    try:
        rc, out, err = run_content(content, command=command, options=run_options)
    except Exception as exc:
        return _handle_run_content_exception(
            root_span=root_span,
            exc=exc,
            services=services,
            command=command,
            command_id=command_id,
            effective_path=effective_path,
        )

    if rc != 0:
        return _handle_nonzero_run_content_result(
            root_span=root_span,
            rc=rc,
            err=err,
            services=services,
            command=command,
            command_id=command_id,
            effective_path=effective_path,
        )

    _handle_degraded_success(
        root_span=root_span,
        err=err,
        options=options,
        services=services,
        command=command,
        command_id=command_id,
        effective_path=effective_path,
    )

    write_failure_rc = _write_output_or_emit_failure(
        root_span=root_span,
        out=out,
        options=options,
        services=services,
        command=command,
        command_id=command_id,
        effective_path=effective_path,
    )
    if write_failure_rc is not None:
        return write_failure_rc

    _safe_set_span_attr(root_span, "flo.exit_code", rc)
    return rc


def _execute(
    path: str | None, command: str, options: dict
) -> int:  # pragma: no cover - integration
    """Read input, run core pipeline, and write output.

    Returns an integer exit code.
    """
    from flo.services import get_services
    from flo.services.telemetry import get_tracer, record_span_success

    services = get_services(verbose=bool(options.get("verbose")))
    telemetry = services.telemetry
    tracer = get_tracer("flo.cli")
    command_id = uuid.uuid4().hex
    try:
        with tracer.start_as_current_span("flo.cli.execute") as root_span:
            root_span.set_attribute("flo.command", command)
            root_span.set_attribute("flo.command_id", command_id)
            root_span.set_attribute("flo.version", _get_flo_version())
            if path:
                root_span.set_attribute("flo.source_path", path)
            rc = _execute_span_body(
                root_span,
                path,
                command,
                options,
                services,
                command_id,
            )
            if rc == 0:
                record_span_success(
                    root_span,
                    event_name="flo.cli.completed",
                    attributes={
                        "flo.exit_code": 0,
                        "flo.command": command,
                        "flo.command_id": command_id,
                    },
                )
            return rc
    finally:
        try:
            telemetry.shutdown()
        except Exception:
            pass


def _build_render_opts(
    verbose: bool,
    output: Optional[str],
    export_fmt: Optional[str],
    diagram: Optional[str],
    render_backend: Optional[str],
    profile: Optional[str],
    detail: Optional[str],
    orientation: Optional[str],
    show_notes: bool,
    no_header: bool,
    no_footer: bool,
    subprocess_view: Optional[str],
    sppm_projection: Optional[str],
    sppm_focus_subprocess: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    layout_spacing: Optional[str],
    publication_page_format: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    sppm_output_profile: Optional[str],
    render_to: Optional[str],
    layout_max_width_px: Optional[str],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
) -> dict:  # pragma: no cover - thin helper
    """Build a normalized options dict from Click-parsed render parameters."""
    opts: dict = {"verbose": verbose, "output": output}
    if export_fmt:
        opts["export"] = export_fmt
    for key, value in (
        ("diagram", diagram),
        ("render_backend", render_backend),
        ("profile", profile),
        ("detail", detail),
        ("orientation", orientation),
        ("subprocess_view", subprocess_view),
        ("sppm_projection", sppm_projection),
        ("sppm_focus_subprocess", sppm_focus_subprocess),
        ("spaghetti_channel", spaghetti_channel),
        ("spaghetti_people_mode", spaghetti_people_mode),
        ("sppm_theme", sppm_theme),
        ("layout_wrap", layout_wrap),
        ("layout_fit", layout_fit),
        ("layout_spacing", layout_spacing),
        ("publication_page_format", publication_page_format),
        ("sppm_step_numbering", sppm_step_numbering),
        ("sppm_label_density", sppm_label_density),
        ("sppm_wrap_strategy", sppm_wrap_strategy),
        ("sppm_truncation_policy", sppm_truncation_policy),
        ("sppm_output_profile", sppm_output_profile),
        ("render_to", render_to),
    ):
        if value is not None:
            opts[key] = value
    for key, value in (
        ("layout_max_width_px", layout_max_width_px),
        ("layout_target_columns", layout_target_columns),
        ("sppm_max_label_step_name", sppm_max_label_step_name),
        ("sppm_max_label_workers", sppm_max_label_workers),
        ("sppm_max_label_ctwt", sppm_max_label_ctwt),
    ):
        if value is not None:
            opts[key] = value
    if show_notes:
        opts["show_notes"] = True
    if no_header:
        opts["no_header"] = True
    if no_footer:
        opts["no_footer"] = True
    return opts


def _apply_render_click_options(*, include_render_to: bool) -> Any:
    """Apply shared render click options from the canonical option schema."""

    def _decorator(func: Any) -> Any:
        for spec in reversed(
            iter_render_option_specs(include_render_to=include_render_to)
        ):
            kwargs: dict[str, Any] = {"help": spec.help_text}
            if spec.is_flag:
                kwargs["is_flag"] = True
            else:
                if spec.choices is not None:
                    kwargs["type"] = click.Choice(list(spec.choices))
                elif spec.value_type is not None:
                    kwargs["type"] = spec.value_type
                if spec.metavar is not None:
                    kwargs["metavar"] = spec.metavar
            func = click.option(spec.flag, **kwargs)(func)
        return func

    return _decorator


# ---------------------------------------------------------------------------
# Click command group
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:  # pragma: no cover - thin CLI layer
    """Click command group for the FLO CLI."""
    pass


@cli.command()
@click.argument("path", required=False)
@click.option("--validate", is_flag=True, help="Only validate file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
@click.option(
    "--export",
    "export_fmt",
    type=click.Choice(["dot", "svg", "json", "ingredients", "movement"]),
    help="Export format (dot is deprecated compatibility-only; prefer svg or json)",
)
@_apply_render_click_options(include_render_to=True)
def run_cmd(
    path: Optional[str],
    validate: bool,
    verbose: bool,
    output: Optional[str],
    export_fmt: Optional[str],
    diagram: Optional[str],
    render_backend: Optional[str],
    profile: Optional[str],
    detail: Optional[str],
    orientation: Optional[str],
    show_notes: bool,
    no_header: bool,
    no_footer: bool,
    subprocess_view: Optional[str],
    sppm_projection: Optional[str],
    sppm_focus_subprocess: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    layout_spacing: Optional[str],
    publication_page_format: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[str],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
    render_to: Optional[str],
) -> None:  # pragma: no cover - integration
    """Render a FLO diagram (default command).

    DOT remains available as a deprecated compatibility-only export surface.
    Prefer SVG for rendered artifacts and JSON for machine-readable export.
    """
    command = "validate" if validate else "run"
    opts = _build_render_opts(
        verbose=verbose,
        output=output,
        export_fmt=export_fmt or "dot",
        diagram=diagram,
        render_backend=render_backend,
        profile=profile,
        detail=detail,
        orientation=orientation,
        show_notes=show_notes,
        no_header=no_header,
        no_footer=no_footer,
        subprocess_view=subprocess_view,
        sppm_projection=sppm_projection,
        sppm_focus_subprocess=sppm_focus_subprocess,
        spaghetti_channel=spaghetti_channel,
        spaghetti_people_mode=spaghetti_people_mode,
        sppm_theme=sppm_theme,
        layout_wrap=layout_wrap,
        layout_fit=layout_fit,
        layout_spacing=layout_spacing,
        publication_page_format=publication_page_format,
        sppm_step_numbering=sppm_step_numbering,
        sppm_label_density=sppm_label_density,
        sppm_wrap_strategy=sppm_wrap_strategy,
        sppm_truncation_policy=sppm_truncation_policy,
        sppm_output_profile=sppm_output_profile,
        render_to=render_to,
        layout_max_width_px=layout_max_width_px,
        layout_target_columns=layout_target_columns,
        sppm_max_label_step_name=sppm_max_label_step_name,
        sppm_max_label_workers=sppm_max_label_workers,
        sppm_max_label_ctwt=sppm_max_label_ctwt,
    )
    rc = _execute(path, command, opts)
    raise SystemExit(rc)


@cli.command("compile")
@click.argument("path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
def compile_cmd(
    path: Optional[str], verbose: bool, output: Optional[str]
) -> None:  # pragma: no cover - integration
    """Compile FLO input and emit a schema-shaped JSON export of the model."""
    rc = _execute(
        path, "compile", {"verbose": verbose, "output": output, "export": "json"}
    )
    raise SystemExit(rc)


@cli.command("validate")
@click.argument("path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def validate_cmd(
    path: Optional[str], verbose: bool
) -> None:  # pragma: no cover - integration
    """Validate FLO input and return non-zero on parse/compile/validation errors."""
    rc = _execute(path, "validate", {"verbose": verbose})
    raise SystemExit(rc)


@cli.command("export")
@click.argument("path", required=False)
@click.option(
    "--export",
    "export_fmt",
    type=click.Choice(["dot", "svg", "json", "ingredients", "movement"]),
    default="dot",
    show_default=True,
    help="Export format (dot is deprecated compatibility-only; prefer svg or json)",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
@_apply_render_click_options(include_render_to=False)
def export_cmd(
    path: Optional[str],
    export_fmt: str,
    verbose: bool,
    output: Optional[str],
    diagram: Optional[str],
    render_backend: Optional[str],
    profile: Optional[str],
    detail: Optional[str],
    orientation: Optional[str],
    show_notes: bool,
    no_header: bool,
    no_footer: bool,
    subprocess_view: Optional[str],
    sppm_projection: Optional[str],
    sppm_focus_subprocess: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    layout_spacing: Optional[str],
    publication_page_format: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[str],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
) -> None:  # pragma: no cover - integration
    """Export FLO input as SVG, JSON, text summaries, or compatibility DOT."""
    opts = _build_render_opts(
        verbose=verbose,
        output=output,
        export_fmt=export_fmt,
        diagram=diagram,
        render_backend=render_backend,
        profile=profile,
        detail=detail,
        orientation=orientation,
        show_notes=show_notes,
        no_header=no_header,
        no_footer=no_footer,
        subprocess_view=subprocess_view,
        sppm_projection=sppm_projection,
        sppm_focus_subprocess=sppm_focus_subprocess,
        spaghetti_channel=spaghetti_channel,
        spaghetti_people_mode=spaghetti_people_mode,
        sppm_theme=sppm_theme,
        layout_wrap=layout_wrap,
        layout_fit=layout_fit,
        layout_spacing=layout_spacing,
        publication_page_format=publication_page_format,
        sppm_step_numbering=sppm_step_numbering,
        sppm_label_density=sppm_label_density,
        sppm_wrap_strategy=sppm_wrap_strategy,
        sppm_truncation_policy=sppm_truncation_policy,
        sppm_output_profile=sppm_output_profile,
        render_to=None,
        layout_max_width_px=layout_max_width_px,
        layout_target_columns=layout_target_columns,
        sppm_max_label_step_name=sppm_max_label_step_name,
        sppm_max_label_workers=sppm_max_label_workers,
        sppm_max_label_ctwt=sppm_max_label_ctwt,
    )
    rc = _execute(path, "export", opts)
    raise SystemExit(rc)


# ---------------------------------------------------------------------------
# Argparse-based entry (for `flo <path>` without explicit subcommand)
# ---------------------------------------------------------------------------


def console_main(argv: list | None = None) -> int:
    """Thin console entry that wires services, IO, and core runners.

    Returns an integer exit code.
    """
    from flo.services.errors import EXIT_USAGE, map_exception_to_rc
    from flo.core._cli_contract import parse_cli_args

    if argv is None:
        argv = sys.argv[1:]

    try:
        parsed = parse_cli_args(argv)
        return _execute(parsed.path, parsed.command, parsed.options)
    except SystemExit as exc:
        code = getattr(exc, "code", EXIT_USAGE)
        return code if isinstance(code, int) else EXIT_USAGE
    except Exception as exc:
        rc, msg, internal = map_exception_to_rc(exc)
        from flo.services import get_services

        services = get_services(verbose=False)
        if internal:
            _emit_error(
                services,
                f"Unexpected error: {msg or 'internal error'}",
                error_kind="internal",
                error_stage="console_main",
                exit_code=rc,
                internal=True,
                command="console_main",
            )
        else:
            _emit_error(
                services,
                msg,
                error_kind="domain",
                error_stage="console_main",
                exit_code=rc,
                internal=False,
                command="console_main",
            )
        return rc


def main(argv: list | None = None) -> int:
    """Programmatic CLI entrypoint.

    Default behavior routes directly to `console_main` so users can run
    `flo <path>` without an explicit subcommand.

    Returns an integer exit code suitable for `sys.exit`.
    """
    return console_main(argv)
