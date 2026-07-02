"""Shared error types and helpers used across FLO layers.

This module is the architecture-neutral home for domain error contracts.
Compatibility imports remain available from ``flo.services.errors``.
"""

from typing import Optional, cast

import structlog
from structlog.stdlib import BoundLogger

# Exit code constants (POSIX-like mapping for CLI semantics)
EXIT_SUCCESS = 0
EXIT_USAGE = 1
EXIT_PARSE_ERROR = 2
EXIT_COMPILE_ERROR = 3
EXIT_VALIDATION_ERROR = 4
EXIT_RENDER_ERROR = 5
# Internal/unexpected error
EXIT_INTERNAL_ERROR = 70


class DomainError(Exception):
    """Base class for expected, domain-level errors.

    Subclasses should provide an ``exit_code`` (int) describing the CLI
    exit code that should be returned to the user. Instances may include
    an optional user-facing message.
    """

    exit_code: int = EXIT_USAGE

    def __init__(
        self,
        message: str | None = None,
        *,
        error_stage: str | None = None,
    ) -> None:
        """Initialize a DomainError with an optional user message."""
        super().__init__(message or "")
        self.error_stage = error_stage


class CLIError(DomainError):
    """Exception type for CLI-level errors that map to non-zero exit codes.

    Backwards-compatible wrapper around ``DomainError`` used throughout
    the codebase.
    """

    def __init__(
        self,
        message: str,
        code: int = EXIT_USAGE,
        *,
        error_stage: str | None = None,
    ) -> None:
        """Initialize a CLIError and set both ``exit_code`` and ``code`` for compatibility."""
        super().__init__(message, error_stage=error_stage)
        self.exit_code = code
        # Keep backwards-compatible attribute name used elsewhere in code/tests
        self.code = code


class ParseError(CLIError):
    """Raised for parse failures (maps to EXIT_PARSE_ERROR)."""

    def __init__(self, message: str, *, error_stage: str | None = None) -> None:
        """Initialize a ParseError mapping to EXIT_PARSE_ERROR."""
        super().__init__(
            message,
            code=EXIT_PARSE_ERROR,
            error_stage=error_stage or "parse",
        )


class CompileError(CLIError):
    """Raised for compile failures (maps to EXIT_COMPILE_ERROR)."""

    def __init__(self, message: str, *, error_stage: str | None = None) -> None:
        """Initialize a CompileError mapping to EXIT_COMPILE_ERROR."""
        super().__init__(
            message,
            code=EXIT_COMPILE_ERROR,
            error_stage=error_stage or "compile",
        )


class ValidationError(CLIError):
    """Raised for validation failures (maps to EXIT_VALIDATION_ERROR)."""

    def __init__(self, message: str, *, error_stage: str | None = None) -> None:
        """Initialize a ValidationError mapping to EXIT_VALIDATION_ERROR."""
        super().__init__(
            message,
            code=EXIT_VALIDATION_ERROR,
            error_stage=error_stage or "validate",
        )


class RenderError(CLIError):
    """Raised for render failures (maps to EXIT_RENDER_ERROR)."""

    def __init__(self, message: str, *, error_stage: str | None = None) -> None:
        """Initialize a RenderError mapping to EXIT_RENDER_ERROR."""
        super().__init__(
            message,
            code=EXIT_RENDER_ERROR,
            error_stage=error_stage or "render",
        )


def map_exception_to_rc(exc: BaseException) -> tuple[int, str, bool, str | None]:
    """Map an exception to a tuple of ``(rc, message, internal, error_stage)``.

    - If ``exc`` is a ``DomainError``/``CLIError``, return
      ``(exit_code, str(exc), False, error_stage)``.
    - Otherwise return ``(EXIT_INTERNAL_ERROR, str(exc) or "internal error", True, None)``.
    """
    if isinstance(exc, DomainError):
        # DomainError instances provide an ``exit_code`` attribute.
        return (
            getattr(exc, "exit_code", EXIT_USAGE),
            str(exc) or "",
            False,
            getattr(exc, "error_stage", None),
        )

    # Fallback: unexpected/internal exceptions
    msg = str(exc) or "internal error"
    return EXIT_INTERNAL_ERROR, msg, True, None


def handle_error(err: str, logger: Optional[BoundLogger] = None) -> None:
    """Handle an error string by logging it via structlog.

    Kept separate so tests can stub or inspect behavior independently.
    """
    if logger is None:
        # ``structlog.get_logger()`` is acceptable as a ``BoundLogger``, but
        # type checkers may still consider ``logger`` Optional; cast to help
        # static analysis.
        logger = cast(BoundLogger, structlog.get_logger())
    logger.error("stderr", message=err)


__all__ = [
    "CLIError",
    "CompileError",
    "DomainError",
    "EXIT_COMPILE_ERROR",
    "EXIT_INTERNAL_ERROR",
    "EXIT_PARSE_ERROR",
    "EXIT_RENDER_ERROR",
    "EXIT_SUCCESS",
    "EXIT_USAGE",
    "EXIT_VALIDATION_ERROR",
    "ParseError",
    "RenderError",
    "ValidationError",
    "handle_error",
    "map_exception_to_rc",
]
