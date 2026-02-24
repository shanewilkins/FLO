"""Error types and helpers used by the CLI and tests."""

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

    Subclasses should provide an `exit_code` (int) describing the CLI
    exit code that should be returned to the user. Instances may include
    an optional user-facing message.
    """

    exit_code: int = EXIT_USAGE

    def __init__(self, message: str | None = None) -> None:
        """Initialize a DomainError with an optional user message."""
        super().__init__(message or "")


class CLIError(DomainError):
    """Exception type for CLI-level errors that map to non-zero exit codes.

    Backwards-compatible wrapper around `DomainError` used throughout
    the codebase.
    """

    def __init__(self, message: str, code: int = EXIT_USAGE) -> None:
        """Initialize a CLIError and set both `exit_code` and `code` for compatibility."""
        super().__init__(message)
        self.exit_code = code
        # Keep backwards-compatible attribute name used elsewhere in code/tests
        self.code = code


class ParseError(CLIError):
    """Raised for parse failures (maps to EXIT_PARSE_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize a ParseError mapping to EXIT_PARSE_ERROR."""
        super().__init__(message, code=EXIT_PARSE_ERROR)


class CompileError(CLIError):
    """Raised for compile failures (maps to EXIT_COMPILE_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize a CompileError mapping to EXIT_COMPILE_ERROR."""
        super().__init__(message, code=EXIT_COMPILE_ERROR)


class ValidationError(CLIError):
    """Raised for validation failures (maps to EXIT_VALIDATION_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize a ValidationError mapping to EXIT_VALIDATION_ERROR."""
        super().__init__(message, code=EXIT_VALIDATION_ERROR)


class RenderError(CLIError):
    """Raised for render failures (maps to EXIT_RENDER_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize a RenderError mapping to EXIT_RENDER_ERROR."""
        super().__init__(message, code=EXIT_RENDER_ERROR)


def map_exception_to_rc(exc: BaseException) -> tuple[int, str, bool]:
    """Map an exception to a tuple of `(rc, message, internal)`.

    - If `exc` is a `DomainError`/`CLIError`, return `(exit_code, str(exc), False)`.
    - Otherwise return `(EXIT_INTERNAL_ERROR, str(exc) or "internal error", True)`.
    """
    if isinstance(exc, DomainError):
        # DomainError instances provide an `exit_code` attribute.
        return getattr(exc, "exit_code", EXIT_USAGE), str(exc) or "", False

    # Fallback: unexpected/internal exceptions
    msg = str(exc) or "internal error"
    return EXIT_INTERNAL_ERROR, msg, True


def handle_error(err: str, logger: Optional[BoundLogger] = None) -> None:
    """Handle an error string by logging it via structlog.

    Kept separate so tests can stub or inspect behavior independently.
    """
    if logger is None:
        # `structlog.get_logger()` is acceptable as a `BoundLogger`, but
        # type checkers may still consider `logger` Optional; cast to help
        # static analysis.
        logger = cast(BoundLogger, structlog.get_logger())
    logger.error("stderr", message=err)
