"""Service construction helpers (logging, telemetry, error handling)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import structlog

from .logging import configure_logging
from . import errors
from .telemetry import init_telemetry, Telemetry


@dataclass
class Services:
    """Container for runtime services used by the CLI.

    Attributes:
        logger: configured `structlog` logger instance.
        error_handler: callable that handles error strings.
        telemetry: telemetry helper object with `shutdown()`.
    """

    logger: structlog.stdlib.BoundLogger
    error_handler: Callable[[str], None]
    telemetry: Telemetry


def get_services(verbose: bool = False) -> Services:
    """Configure and return runtime services for the CLI.

    - Configures logging (idempotent).
    - Returns a `Services` object containing a `logger` and a
      simple `error_handler` function bound to that logger.
    """
    import logging

    level = logging.DEBUG if verbose else logging.INFO
    configure_logging(level=level)
    logger = structlog.get_logger()

    def _error_handler(msg: str) -> None:
        # Delegate to the central `errors.handle_error` so behaviour is
        # consistent and testable across the codebase.
        errors.handle_error(msg, logger)

    # Initialize telemetry (returns a no-op Telemetry if OTEL not installed).
    telemetry = init_telemetry(service_name="flo", console_export=True)

    return Services(logger=logger, error_handler=_error_handler, telemetry=telemetry)
