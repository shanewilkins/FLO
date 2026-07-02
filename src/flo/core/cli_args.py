"""CLI argument parsing and helpers placed under core package."""

from __future__ import annotations

from typing import Tuple

from flo.core.render_option_schema import (
    add_argparse_render_options,
    build_render_options_from_namespace,
)
from flo.services import get_services, Services
from structlog.stdlib import BoundLogger


def parse_args(
    argv: list | None, services: Services
) -> Tuple[str | None, str, dict, Services, BoundLogger]:
    """Parse CLI arguments and return (path, command, options, services, logger).

    This is a thin wrapper around argparse that returns normalized
    command, options and a services/logger pair for downstream use.
    """
    import argparse

    command = "run"
    options: dict = {}
    path: str | None = None
    logger = services.logger

    if argv is None:
        return path, command, options, services, logger

    parser = argparse.ArgumentParser(prog="flo")
    parser.add_argument(
        "command_or_path",
        nargs="?",
        help="Command (run/compile/validate/export) or path",
    )
    parser.add_argument("path", nargs="?", help="Path to .flo file (or - for stdin)")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    parser.add_argument(
        "--validate", action="store_true", help="Only validate the file"
    )
    parser.add_argument(
        "--export",
        choices=["svg", "json", "ingredients", "movement"],
        help="Export format (svg for diagrams, json for machine-readable output)",
    )
    parser.add_argument(
        "--format",
        choices=["svg", "json", "ingredients", "movement"],
        help=argparse.SUPPRESS,
    )
    add_argparse_render_options(parser, include_render_to=True)
    parsed = parser.parse_args(argv)

    supported_commands = {"run", "compile", "validate", "export"}
    first = parsed.command_or_path
    second = parsed.path

    command, path = _resolve_command_and_path(
        first=first, second=second, supported_commands=supported_commands
    )
    options.update(_build_options_from_parsed(parsed))

    if parsed.validate:
        command = "validate"

    if command in {"run", "export"} and "export" not in options:
        options["export"] = "svg"
    if command == "compile" and "export" not in options:
        options["export"] = "json"

    if options.get("verbose"):
        services = get_services(verbose=True)
        logger = services.logger

    return path, command, options, services, logger


def _resolve_command_and_path(
    first: str | None, second: str | None, supported_commands: set[str]
) -> tuple[str, str | None]:
    if first in supported_commands:
        return str(first), second
    return "run", first


def _build_options_from_parsed(parsed: object) -> dict:
    export_value = getattr(parsed, "export", None) or getattr(parsed, "format", None)
    options: dict = {
        "verbose": bool(getattr(parsed, "verbose", False)),
        "output": getattr(parsed, "output", None),
    }
    options.update(build_render_options_from_namespace(parsed, include_render_to=True))

    if export_value:
        options["export"] = export_value

    return options
