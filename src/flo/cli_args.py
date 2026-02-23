"""CLI argument parsing and service reconfiguration helper.

Provides `parse_args(argv, services)` which returns
(path, command, options, services, logger).
"""

from __future__ import annotations

from typing import Tuple

from flo.services import get_services, Services
from structlog.stdlib import BoundLogger

def parse_args(argv: list | None, services: Services) -> Tuple[str | None, str, dict, Services, BoundLogger]:
    """Parse CLI arguments and optionally reconfigure `services`.

    Returns a tuple: `(path, command, options, services, logger)` suitable
    for use by the programmatic entrypoints.
    """
    import argparse

    command = "compile"
    options: dict = {}
    path: str | None = None
    logger = services.logger

    if argv is None:
        return path, command, options, services, logger

    parser = argparse.ArgumentParser(prog="flo")
    parser.add_argument("path", nargs="?", help="Path to .flo file (or - for stdin)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    parser.add_argument("--validate", action="store_true", help="Only validate the file")
    parsed = parser.parse_args(argv)
    path = parsed.path
    options["verbose"] = bool(parsed.verbose)
    options["output"] = parsed.output
    if parsed.validate:
        command = "validate"

    if options.get("verbose"):
        services = get_services(verbose=True)
        logger = services.logger

    return path, command, options, services, logger
