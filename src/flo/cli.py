"""Command-line interface (Click) thin wrapper for programmatic core."""

from __future__ import annotations

import sys
from typing import Optional

import click
from rich.console import Console

from flo import main as main_module


console = Console()


@click.group()
def cli() -> None:  # pragma: no cover - thin CLI layer
    """FLO command-line interface (thin wrapper).

    This module intentionally keeps CLI logic minimal and delegates to
    the programmatic `flo.main` functions so tests exercise the core
    functionality without invoking Click.
    """
    pass


@cli.command()
@click.argument("path", required=False)
@click.option("--validate", is_flag=True, help="Only validate file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-o", "--output", help="Write output to file")
def run_cmd(path: Optional[str], validate: bool, verbose: bool, output: Optional[str]) -> None:  # pragma: no cover - integration
    """Run or validate a .flo file. Use '-' for stdin."""
    # Delegate to the programmatic `main` orchestrator to keep CLI thin.
    args: list[str] = []
    if path:
        args.append(path)
    if validate:
        args.append("--validate")
    if verbose:
        args.append("-v")
    if output:
        args.extend(["-o", output])

    # Call the console-oriented entrypoint which implements full CLI semantics.
    rc = console_main(args)
    raise SystemExit(rc)


def console_main(argv: list | None = None) -> int:  # pragma: no cover - thin wrapper
    """Console entrypoint that mirrors the previous `main.console_main`.

    Kept here so Click-based invocation and the CLI runner can share the
    same codepath without compatibility shims living in `main.py`.
    """
    from flo.services import get_services
    from flo.cli_args import parse_args
    from flo.io import read_input, write_output
    from flo.core import run_content
    from flo.adapters import parse_adapter
    from flo.compiler import compile_adapter
    from flo.ir import validate_ir
    from flo.analysis import scc_condense
    from flo.render import render_dot
    from flo.services.errors import (
        CLIError,
        EXIT_USAGE,
        EXIT_RENDER_ERROR,
    )

    services = get_services(verbose=False)
    logger = services.logger

    if argv is None:
        argv = sys.argv[1:]

    path, command, options, services, logger = parse_args(argv, services)
    telemetry = services.telemetry

    # Read input
    rc, content, err = (0, "", "")
    if path:
        rc, content, err = read_input(path)
    else:
        rc, content, err = read_input("-")
    if rc != 0:
        services.error_handler(err)
        return rc

    # Process content (parse/compile/validate)
    try:
        rc, out, err = run_content(content, command=command, options=options)
    except CLIError as e:
        services.error_handler(str(e))
        return getattr(e, "code", EXIT_USAGE)
    except Exception as e:  # pragma: no cover - unexpected
        services.error_handler(f"Unexpected error: {e}")
        return EXIT_USAGE

    # Output
    write_rc, write_err = write_output(out, options.get("output") if options else None)
    if write_rc != 0:
        services.error_handler(write_err)
        return write_rc

    # Best-effort telemetry shutdown
    try:
        telemetry.shutdown()
    except Exception:
        pass

    return rc


def main(argv: list | None = None) -> int:  # pragma: no cover - CLI entry
    """Entrypoint shim for setup.py/console script.

    Accepts an optional argv list (useful for programmatic invocation).
    Returns an exit code.
    """
    if argv is None:
        # let click handle sys.argv
        cli()
        return 0
    # When argv is provided, invoke Click programmatically.
    try:
        cli.main(args=argv, prog_name="flo")
        return 0
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
