"""Service construction helpers (logging, telemetry, error handling)."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Callable

import structlog

from .logging import configure_logging
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
        # Human-facing CLI diagnostics must stay concise. Structured runtime
        # context belongs in telemetry rather than in ordinary stderr.
        print(msg, file=sys.stderr)

    # Initialize telemetry (returns a no-op Telemetry if OTEL not installed).
    # Keep CLI stdout deterministic (e.g., JSON/DOT exports) by default.
    telemetry = init_telemetry(service_name="flo", console_export=False)

    return Services(logger=logger, error_handler=_error_handler, telemetry=telemetry)
