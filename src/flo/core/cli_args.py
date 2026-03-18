"""CLI argument parsing and helpers placed under core package."""
from __future__ import annotations

from typing import Tuple

from flo.services import get_services, Services
from structlog.stdlib import BoundLogger


def parse_args(argv: list | None, services: Services) -> Tuple[str | None, str, dict, Services, BoundLogger]:
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
    parser.add_argument("command_or_path", nargs="?", help="Command (run/compile/validate/export) or path")
    parser.add_argument("path", nargs="?", help="Path to .flo file (or - for stdin)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    parser.add_argument("--validate", action="store_true", help="Only validate the file")
    parser.add_argument("--export", choices=["dot", "json", "ingredients", "movement"], help="Export format (dot|json|ingredients|movement)")
    parser.add_argument("--format", choices=["dot", "json", "ingredients", "movement"], help=argparse.SUPPRESS)
    parser.add_argument("--diagram", choices=["flowchart", "swimlane", "spaghetti"], help="Diagram type for DOT output")
    parser.add_argument("--profile", choices=["default", "analysis"], help="Projection rule profile")
    parser.add_argument("--detail", choices=["summary", "standard", "verbose"], help="Detail level")
    parser.add_argument("--orientation", choices=["lr", "tb"], help="Layout orientation for DOT output")
    parser.add_argument("--show-notes", action="store_true", help="Include node notes in DOT labels")
    parser.add_argument("--subprocess-view", choices=["expanded", "parent-only"], help="Subprocess rendering mode")
    parser.add_argument(
        "--spaghetti-channel",
        choices=["both", "material", "people"],
        help="Movement channel for spaghetti diagrams",
    )
    parser.add_argument(
        "--spaghetti-people-mode",
        choices=["worker", "aggregate"],
        help="People trace mode for spaghetti diagrams",
    )
    parsed = parser.parse_args(argv)

    supported_commands = {"run", "compile", "validate", "export"}
    first = parsed.command_or_path
    second = parsed.path

    command, path = _resolve_command_and_path(first=first, second=second, supported_commands=supported_commands)
    options.update(_build_options_from_parsed(parsed))

    if parsed.validate:
        command = "validate"

    if command in {"run", "export"} and "export" not in options:
        options["export"] = "dot"
    if command == "compile" and "export" not in options:
        options["export"] = "json"

    if options.get("verbose"):
        services = get_services(verbose=True)
        logger = services.logger

    return path, command, options, services, logger


def _resolve_command_and_path(first: str | None, second: str | None, supported_commands: set[str]) -> tuple[str, str | None]:
    if first in supported_commands:
        return str(first), second
    return "run", first


def _build_options_from_parsed(parsed: object) -> dict:
    export_value = getattr(parsed, "export", None) or getattr(parsed, "format", None)
    options: dict = {
        "verbose": bool(getattr(parsed, "verbose", False)),
        "output": getattr(parsed, "output", None),
    }

    for key in (
        "diagram",
        "profile",
        "detail",
        "orientation",
        "subprocess_view",
        "spaghetti_channel",
        "spaghetti_people_mode",
    ):
        value = getattr(parsed, key, None)
        if value:
            options[key] = value

    if export_value:
        options["export"] = export_value
    if bool(getattr(parsed, "show_notes", False)):
        options["show_notes"] = True

    return options
