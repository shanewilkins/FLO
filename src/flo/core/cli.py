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
def run_cmd(path: Optional[str], validate: bool, verbose: bool, output: Optional[str]) -> None:  # pragma: no cover - integration
    """Invoke the CLI command handler with normalized arguments."""
    args: list[str] = []
    if path:
        args.append(path)
    if validate:
        args.append("--validate")
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
    """Programmatic CLI entrypoint; if `argv` is None runs the Click CLI.

    Returns an integer exit code suitable for `sys.exit`.
    """
    if argv is None:
        cli()
        return 0
    try:
        cli.main(args=argv, prog_name="flo")
        return 0
    except SystemExit as e:
        return int(getattr(e, "code", 0) or 0)
