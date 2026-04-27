"""CLI helpers moved under `core` package."""
from __future__ import annotations

import sys
from typing import Optional

import click


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
@click.option("--diagram", type=click.Choice(["flowchart", "swimlane", "spaghetti", "sppm"]), help="Diagram type for DOT output")
@click.option("--profile", type=click.Choice(["default", "analysis"]), help="Projection rule profile")
@click.option("--detail", type=click.Choice(["summary", "standard", "verbose"]), help="Detail level")
@click.option("--orientation", type=click.Choice(["lr", "tb"]), help="Layout orientation for DOT output")
@click.option("--show-notes", is_flag=True, help="Include node notes in DOT labels")
@click.option("--subprocess-view", type=click.Choice(["expanded", "parent-only"]), help="Subprocess rendering mode")
@click.option("--spaghetti-channel", type=click.Choice(["both", "material", "people"]), help="Movement channel for spaghetti diagrams")
@click.option("--spaghetti-people-mode", type=click.Choice(["worker", "aggregate"]), help="People trace mode for spaghetti diagrams")
@click.option("--sppm-theme", type=click.Choice(["default", "print", "monochrome"]), help="Color theme for SPPM diagrams")
@click.option("--layout-wrap", type=click.Choice(["auto", "off"]), help="Shared autoformat wrapping mode (orientation-aware)")
@click.option("--layout-fit", type=click.Choice(["fit-preferred", "fit-strict"]), help="Shared autoformat fit mode")
@click.option("--sppm-step-numbering", type=click.Choice(["off", "node", "edge"]), help="SPPM step numbering mode")
@click.option("--sppm-label-density", type=click.Choice(["full", "compact", "teaching"]), help="SPPM label density mode")
@click.option("--sppm-wrap-strategy", type=click.Choice(["word", "balanced", "hard"]), help="Text wrapping strategy for SPPM labels")
@click.option("--sppm-truncation-policy", type=click.Choice(["ellipsis", "clip", "none"]), help="Label truncation policy for SPPM text")
@click.option("--layout-max-width-px", type=int, help="Max layout width hint for autoformat wrapping")
@click.option("--layout-target-columns", type=int, help="Target columns/steps per wrapped chunk")
@click.option("--sppm-max-label-step-name", type=int, help="Max step-name label length for SPPM")
@click.option("--sppm-max-label-workers", type=int, help="Max workers label length for SPPM")
@click.option("--sppm-max-label-ctwt", type=int, help="Max CT/WT label length for SPPM")
@click.option("--sppm-output-profile", type=click.Choice(["default", "book", "web", "print", "slide"]), help="SPPM output profile preset")
@click.option("--render-to", metavar="FILE", help="Render DOT output to an image file via Graphviz")
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
    subprocess_view: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[int],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
    render_to: Optional[str],
) -> None:  # pragma: no cover - integration
    """Invoke the CLI command handler with normalized arguments."""
    args = _build_run_args(
        path=path,
        validate=validate,
        verbose=verbose,
        output=output,
        export_fmt=export_fmt,
        diagram=diagram,
        profile=profile,
        detail=detail,
        orientation=orientation,
        show_notes=show_notes,
        subprocess_view=subprocess_view,
        spaghetti_channel=spaghetti_channel,
        spaghetti_people_mode=spaghetti_people_mode,
        sppm_theme=sppm_theme,
        layout_wrap=layout_wrap,
        layout_fit=layout_fit,
        sppm_step_numbering=sppm_step_numbering,
        sppm_label_density=sppm_label_density,
        sppm_wrap_strategy=sppm_wrap_strategy,
        sppm_truncation_policy=sppm_truncation_policy,
        layout_max_width_px=layout_max_width_px,
        layout_target_columns=layout_target_columns,
        sppm_max_label_step_name=sppm_max_label_step_name,
        sppm_max_label_workers=sppm_max_label_workers,
        sppm_max_label_ctwt=sppm_max_label_ctwt,
        sppm_output_profile=sppm_output_profile,
        render_to=render_to,
    )
    rc = console_main(args)
    raise SystemExit(rc)


def _build_run_args(  # pragma: no cover - thin click shim helper
    *,
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
    subprocess_view: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[int],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
    render_to: Optional[str],
) -> list[str]:
    """Build argparse-style argv list from Click-parsed keyword arguments."""
    args: list[str] = ["run"]
    if path:
        args.append(path)
    if validate:
        args.append("--validate")
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])
    # flag → argparse-name pairs (all optional string args)
    pairs: list[tuple[Optional[str], str]] = [
        (export_fmt, "--export"),
        (diagram, "--diagram"),
        (profile, "--profile"),
        (detail, "--detail"),
        (orientation, "--orientation"),
        (subprocess_view, "--subprocess-view"),
        (spaghetti_channel, "--spaghetti-channel"),
        (spaghetti_people_mode, "--spaghetti-people-mode"),
        (sppm_theme, "--sppm-theme"),
        (layout_wrap, "--layout-wrap"),
        (layout_fit, "--layout-fit"),
        (sppm_step_numbering, "--sppm-step-numbering"),
        (sppm_label_density, "--sppm-label-density"),
        (sppm_wrap_strategy, "--sppm-wrap-strategy"),
        (sppm_truncation_policy, "--sppm-truncation-policy"),
        (sppm_output_profile, "--sppm-output-profile"),
        (render_to, "--render-to"),
    ]
    for value, flag in pairs:
        if value:
            args.extend([flag, value])
    for value, flag in [
        (layout_max_width_px, "--layout-max-width-px"),
        (layout_target_columns, "--layout-target-columns"),
        (sppm_max_label_step_name, "--sppm-max-label-step-name"),
        (sppm_max_label_workers, "--sppm-max-label-workers"),
        (sppm_max_label_ctwt, "--sppm-max-label-ctwt"),
    ]:
        if value is not None:
            args.extend([flag, str(value)])
    if show_notes:
        args.append("--show-notes")
    return args


@cli.command("compile")
@click.argument("path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
def compile_cmd(path: Optional[str], verbose: bool, output: Optional[str]) -> None:  # pragma: no cover - integration
    """Compile FLO input and emit a schema-shaped JSON export of the model."""
    args: list[str] = ["compile"]
    if path:
        args.append(path)
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])
    rc = console_main(args)
    raise SystemExit(rc)


@cli.command("validate")
@click.argument("path", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def validate_cmd(path: Optional[str], verbose: bool) -> None:  # pragma: no cover - integration
    """Validate FLO input and return non-zero on parse/compile/validation errors."""
    args: list[str] = ["validate"]
    if path:
        args.append(path)
    if verbose:
        args.append("-v")
    rc = console_main(args)
    raise SystemExit(rc)


@cli.command("export")
@click.argument("path", required=False)
@click.option("--export", "export_fmt", type=click.Choice(["dot", "json", "ingredients", "movement"]), default="dot", show_default=True)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
@click.option("--diagram", type=click.Choice(["flowchart", "swimlane", "spaghetti", "sppm"]), help="Diagram type for DOT output")
@click.option("--profile", type=click.Choice(["default", "analysis"]), help="Projection rule profile")
@click.option("--detail", type=click.Choice(["summary", "standard", "verbose"]), help="Detail level")
@click.option("--orientation", type=click.Choice(["lr", "tb"]), help="Layout orientation for DOT output")
@click.option("--show-notes", is_flag=True, help="Include node notes in DOT labels")
@click.option("--subprocess-view", type=click.Choice(["expanded", "parent-only"]), help="Subprocess rendering mode")
@click.option("--spaghetti-channel", type=click.Choice(["both", "material", "people"]), help="Movement channel for spaghetti diagrams")
@click.option("--spaghetti-people-mode", type=click.Choice(["worker", "aggregate"]), help="People trace mode for spaghetti diagrams")
@click.option("--sppm-theme", type=click.Choice(["default", "print", "monochrome"]), help="Color theme for SPPM diagrams")
@click.option("--layout-wrap", type=click.Choice(["auto", "off"]), help="Shared autoformat wrapping mode (orientation-aware)")
@click.option("--layout-fit", type=click.Choice(["fit-preferred", "fit-strict"]), help="Shared autoformat fit mode")
@click.option("--sppm-step-numbering", type=click.Choice(["off", "node", "edge"]), help="SPPM step numbering mode")
@click.option("--sppm-label-density", type=click.Choice(["full", "compact", "teaching"]), help="SPPM label density mode")
@click.option("--sppm-wrap-strategy", type=click.Choice(["word", "balanced", "hard"]), help="Text wrapping strategy for SPPM labels")
@click.option("--sppm-truncation-policy", type=click.Choice(["ellipsis", "clip", "none"]), help="Label truncation policy for SPPM text")
@click.option("--layout-max-width-px", type=int, help="Max layout width hint for autoformat wrapping")
@click.option("--layout-target-columns", type=int, help="Target columns/steps per wrapped chunk")
@click.option("--sppm-max-label-step-name", type=int, help="Max step-name label length for SPPM")
@click.option("--sppm-max-label-workers", type=int, help="Max workers label length for SPPM")
@click.option("--sppm-max-label-ctwt", type=int, help="Max CT/WT label length for SPPM")
@click.option("--sppm-output-profile", type=click.Choice(["default", "book", "web", "print", "slide"]), help="SPPM output profile preset")
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
    subprocess_view: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[int],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
) -> None:  # pragma: no cover - integration
    """Export FLO input as DOT or JSON."""
    args = _build_export_args(
        path=path,
        export_fmt=export_fmt,
        verbose=verbose,
        output=output,
        diagram=diagram,
        profile=profile,
        detail=detail,
        orientation=orientation,
        show_notes=show_notes,
        subprocess_view=subprocess_view,
        spaghetti_channel=spaghetti_channel,
        spaghetti_people_mode=spaghetti_people_mode,
        sppm_theme=sppm_theme,
        layout_wrap=layout_wrap,
        layout_fit=layout_fit,
        sppm_step_numbering=sppm_step_numbering,
        sppm_label_density=sppm_label_density,
        sppm_wrap_strategy=sppm_wrap_strategy,
        sppm_truncation_policy=sppm_truncation_policy,
        layout_max_width_px=layout_max_width_px,
        layout_target_columns=layout_target_columns,
        sppm_max_label_step_name=sppm_max_label_step_name,
        sppm_max_label_workers=sppm_max_label_workers,
        sppm_max_label_ctwt=sppm_max_label_ctwt,
        sppm_output_profile=sppm_output_profile,
    )
    rc = console_main(args)
    raise SystemExit(rc)


def _build_export_args(  # pragma: no cover - thin click shim helper
    *,
    path: Optional[str],
    export_fmt: str,
    verbose: bool,
    output: Optional[str],
    diagram: Optional[str],
    profile: Optional[str],
    detail: Optional[str],
    orientation: Optional[str],
    show_notes: bool,
    subprocess_view: Optional[str],
    spaghetti_channel: Optional[str],
    spaghetti_people_mode: Optional[str],
    sppm_theme: Optional[str],
    layout_wrap: Optional[str],
    layout_fit: Optional[str],
    sppm_step_numbering: Optional[str],
    sppm_label_density: Optional[str],
    sppm_wrap_strategy: Optional[str],
    sppm_truncation_policy: Optional[str],
    layout_max_width_px: Optional[int],
    layout_target_columns: Optional[int],
    sppm_max_label_step_name: Optional[int],
    sppm_max_label_workers: Optional[int],
    sppm_max_label_ctwt: Optional[int],
    sppm_output_profile: Optional[str],
) -> list[str]:
    args: list[str] = ["export"]
    if path:
        args.append(path)
    args.extend(["--export", export_fmt])
    _append_click_string_pairs(
        args,
        [
            (diagram, "--diagram"),
            (profile, "--profile"),
            (detail, "--detail"),
            (orientation, "--orientation"),
            (subprocess_view, "--subprocess-view"),
            (spaghetti_channel, "--spaghetti-channel"),
            (spaghetti_people_mode, "--spaghetti-people-mode"),
            (sppm_theme, "--sppm-theme"),
            (layout_wrap, "--layout-wrap"),
            (layout_fit, "--layout-fit"),
            (sppm_step_numbering, "--sppm-step-numbering"),
            (sppm_label_density, "--sppm-label-density"),
            (sppm_wrap_strategy, "--sppm-wrap-strategy"),
            (sppm_truncation_policy, "--sppm-truncation-policy"),
            (sppm_output_profile, "--sppm-output-profile"),
        ],
    )
    _append_click_int_pairs(
        args,
        [
            (layout_max_width_px, "--layout-max-width-px"),
            (layout_target_columns, "--layout-target-columns"),
            (sppm_max_label_step_name, "--sppm-max-label-step-name"),
            (sppm_max_label_workers, "--sppm-max-label-workers"),
            (sppm_max_label_ctwt, "--sppm-max-label-ctwt"),
        ],
    )
    if show_notes:
        args.append("--show-notes")
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])
    return args


def _append_click_string_pairs(args: list[str], pairs: list[tuple[Optional[str], str]]) -> None:
    for value, flag in pairs:
        if value:
            args.extend([flag, value])


def _append_click_int_pairs(args: list[str], pairs: list[tuple[Optional[int], str]]) -> None:
    for value, flag in pairs:
        if value is not None:
            args.extend([flag, str(value)])


def console_main(argv: list | None = None) -> int:  # pragma: no cover - thin wrapper
    """Thin console entry that wires services, IO, and core runners.

    Returns an integer exit code.
    """
    from flo.services import get_services
    from flo.core import run_content
    from flo.services.io import read_input, write_output
    from flo.services.errors import CLIError, EXIT_USAGE

    services = get_services(verbose=False)
    logger = services.logger

    if argv is None:
        argv = sys.argv[1:]

    from flo.core.cli_args import parse_args  # local import to avoid cycle

    path, command, options, services, logger = parse_args(argv, services)
    telemetry = services.telemetry

    rc, content, err = read_input(path) if path else read_input("-")
    if rc != 0:
        services.error_handler(err)
        return rc

    run_options = dict(options or {})
    if path and path != "-":
        run_options.setdefault("source_path", path)

    try:
        rc, out, err = run_content(content, command=command, options=run_options)
    except CLIError as e:
        services.error_handler(str(e))
        return getattr(e, "code", EXIT_USAGE)
    except Exception as e:
        services.error_handler(f"Unexpected error: {e}")
        return EXIT_USAGE

    if out:
        write_rc, write_err = write_output(out, options.get("output") if options else None)
        if write_rc != 0:
            services.error_handler(write_err)
            return write_rc

    try:
        telemetry.shutdown()
    except Exception:
        pass

    return rc


def main(argv: list | None = None) -> int:  # pragma: no cover - CLI entry
    """Programmatic CLI entrypoint.

    Default behavior routes directly to `console_main` so users can run
    `flo <path>` without an explicit subcommand.

    Returns an integer exit code suitable for `sys.exit`.
    """
    return console_main(argv)
