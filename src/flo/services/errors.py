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


class CLIError(Exception):
    """Exception type for CLI-level errors that map to non-zero exit codes.

    Args:
        message: Human-friendly error message.
        code: Exit code to return (one of the EXIT_* constants).
    """

    def __init__(self, message: str, code: int = EXIT_USAGE) -> None:
        """Create a `CLIError` with message and exit `code`."""
        super().__init__(message)
        self.code = code


class ParseError(CLIError):
    """Raised for parse failures (maps to EXIT_PARSE_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize ParseError."""
        super().__init__(message, code=EXIT_PARSE_ERROR)


class CompileError(CLIError):
    """Raised for compile failures (maps to EXIT_COMPILE_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize CompileError."""
        super().__init__(message, code=EXIT_COMPILE_ERROR)


class ValidationError(CLIError):
    """Raised for validation failures (maps to EXIT_VALIDATION_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize ValidationError."""
        super().__init__(message, code=EXIT_VALIDATION_ERROR)


class RenderError(CLIError):
    """Raised for render failures (maps to EXIT_RENDER_ERROR)."""

    def __init__(self, message: str) -> None:
        """Initialize RenderError."""
        super().__init__(message, code=EXIT_RENDER_ERROR)


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
