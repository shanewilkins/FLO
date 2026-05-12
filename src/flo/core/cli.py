"""CLI entry points for the FLO tool."""
from __future__ import annotations

import sys
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


def _execute_span_body(root_span: Any, path: str | None, command: str, options: dict, services: Any) -> int:
    """Run the FLO pipeline within an existing trace span.

    Returns an integer exit code.
    """
    from flo.core import run_content
    from flo.services.io import read_input, write_output
    from flo.services.errors import map_exception_to_rc
    from flo.services.telemetry import record_span_error

    effective_path = path or "-"
    rc, content, err = read_input(effective_path)
    if rc != 0:
        record_span_error(root_span, err or "")
        _emit_error(
            services, err,
            error_kind="io", error_stage="read_input",
            exit_code=rc, internal=False, command=command, path=effective_path,
        )
        return rc

    run_options = dict(options)
    if path and path != "-":
        run_options.setdefault("source_path", path)

    try:
        rc, out, err = run_content(content, command=command, options=run_options)
    except Exception as exc:
        mapped_rc, msg, internal = map_exception_to_rc(exc)
        record_span_error(root_span, msg or "")
        display_msg = f"Unexpected error: {msg or 'internal error'}" if internal else msg
        _emit_error(
            services, display_msg,
            error_kind="internal" if internal else "domain",
            error_stage="run_content",
            exit_code=mapped_rc, internal=internal, command=command, path=effective_path,
        )
        return mapped_rc

    if out:
        write_rc, write_err = write_output(out, options.get("output"))
        if write_rc != 0:
            record_span_error(root_span, write_err or "")
            _emit_error(
                services, write_err,
                error_kind="io", error_stage="write_output",
                exit_code=write_rc, internal=False, command=command, path=effective_path,
            )
            return write_rc

    return rc


def _execute(path: str | None, command: str, options: dict) -> int:  # pragma: no cover - integration
    """Read input, run core pipeline, and write output.

    Returns an integer exit code.
    """
    from flo.services import get_services
    from flo.services.telemetry import get_tracer

    services = get_services(verbose=bool(options.get("verbose")))
    telemetry = services.telemetry
    tracer = get_tracer("flo.cli")
    try:
        with tracer.start_as_current_span("flo.cli.execute") as root_span:
            root_span.set_attribute("flo.command", command)
            root_span.set_attribute("flo.version", _get_flo_version())
            if path:
                root_span.set_attribute("flo.source_path", path)
            return _execute_span_body(root_span, path, command, options, services)
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
        for spec in reversed(iter_render_option_specs(include_render_to=include_render_to)):
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
@click.option("--export", "export_fmt", type=click.Choice(["dot", "json", "ingredients", "movement"]), help="Export format")
@_apply_render_click_options(include_render_to=True)
def run_cmd(
    path: Optional[str],
    validate: bool,
    verbose: bool,
    output: Optional[str],
    export_fmt: Optional[str],
    diagram: Optional[str],
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
    """Render a FLO diagram (default command)."""
    command = "validate" if validate else "run"
    opts = _build_render_opts(
        verbose=verbose,
        output=output,
        export_fmt=export_fmt or "dot",
        diagram=diagram,
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
def compile_cmd(path: Optional[str], verbose: bool, output: Optional[str]) -> None:  # pragma: no cover - integration
    """Compile FLO input and emit a schema-shaped JSON export of the model."""
    rc = _execute(path, "compile", {"verbose": verbose, "output": output, "export": "json"})
    raise SystemExit(rc)


@cli.command("validate")
@click.argument("path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def validate_cmd(path: Optional[str], verbose: bool) -> None:  # pragma: no cover - integration
    """Validate FLO input and return non-zero on parse/compile/validation errors."""
    rc = _execute(path, "validate", {"verbose": verbose})
    raise SystemExit(rc)


@cli.command("export")
@click.argument("path", required=False)
@click.option("--export", "export_fmt", type=click.Choice(["dot", "json", "ingredients", "movement"]), default="dot", show_default=True)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
@_apply_render_click_options(include_render_to=False)
def export_cmd(
    path: Optional[str],
    export_fmt: str,
    verbose: bool,
    output: Optional[str],
    diagram: Optional[str],
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
    """Export FLO input as DOT or JSON."""
    opts = _build_render_opts(
        verbose=verbose,
        output=output,
        export_fmt=export_fmt,
        diagram=diagram,
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
