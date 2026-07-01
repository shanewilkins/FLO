"""Compatibility re-export for shared FLO error contracts.

Prefer importing from ``flo.errors`` for architecture-neutral dependencies.
This module remains as a shim for existing call sites.
"""

from flo.errors import (  # noqa: F401
    CLIError,
    CompileError,
    DomainError,
    EXIT_COMPILE_ERROR,
    EXIT_INTERNAL_ERROR,
    EXIT_PARSE_ERROR,
    EXIT_RENDER_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE,
    EXIT_VALIDATION_ERROR,
    ParseError,
    RenderError,
    ValidationError,
    handle_error,
    map_exception_to_rc,
)

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
