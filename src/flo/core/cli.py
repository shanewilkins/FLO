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
@click.option("--export", "export_fmt", type=click.Choice(["dot", "json"]), help="Export format")
def run_cmd(path: Optional[str], validate: bool, verbose: bool, output: Optional[str], export_fmt: Optional[str]) -> None:  # pragma: no cover - integration
    """Invoke the CLI command handler with normalized arguments."""
    args: list[str] = []
    args.append("run")
    if path:
        args.append(path)
    if validate:
        args.append("--validate")
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])
    if export_fmt:
        args.extend(["--export", export_fmt])

    rc = console_main(args)
    raise SystemExit(rc)


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
@click.option("--export", "export_fmt", type=click.Choice(["dot", "json"]), default="dot", show_default=True)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
def export_cmd(path: Optional[str], export_fmt: str, verbose: bool, output: Optional[str]) -> None:  # pragma: no cover - integration
    """Export FLO input as DOT or JSON."""
    args: list[str] = ["export"]
    if path:
        args.append(path)
    args.extend(["--export", export_fmt])
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])
    rc = console_main(args)
    raise SystemExit(rc)


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

    try:
        rc, out, err = run_content(content, command=command, options=options)
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
