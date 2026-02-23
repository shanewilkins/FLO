from __future__ import annotations

import sys
from typing import Optional

import click
from rich.console import Console

from flo.services import get_services
from flo.main import run_file, run


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
    services = get_services(verbose=verbose)
    try:
        if validate:
            command = "validate"
        else:
            command = "compile"

        if path:
            rc, out, err = run_file(path, command=command, options={"output": output, "verbose": verbose})
        else:
            rc, out, err = run()

        if out:
            console.print(out)
        if err:
            console.print(err, style="red", file=sys.stderr)
        raise SystemExit(rc)
    finally:
        try:
            services.telemetry.shutdown()
        except Exception:
            pass


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
