"""Compatibility console entry for implicit ``flo <path>`` invocation."""

from __future__ import annotations

import sys
from typing import Any, Callable


def console_main(
    argv: list | None = None,
    *,
    execute_request: Callable[[Any], int],
    emit_error: Callable[..., None],
) -> int:
    """Execute the compatibility parser and return a process exit code."""
    from flo.core._cli_contract import parse_cli_args
    from flo.services.errors import EXIT_USAGE, map_exception_to_rc

    args = sys.argv[1:] if argv is None else argv
    try:
        parsed = parse_cli_args(args)
        return execute_request(parsed)
    except SystemExit as exc:
        code = getattr(exc, "code", EXIT_USAGE)
        return code if isinstance(code, int) else EXIT_USAGE
    except Exception as exc:
        rc, msg, internal, error_stage = map_exception_to_rc(exc)
        _emit_console_error(
            emit_error=emit_error,
            rc=rc,
            message=msg,
            internal=internal,
            error_stage=error_stage,
        )
        return rc


def _emit_console_error(
    *,
    emit_error: Callable[..., None],
    rc: int,
    message: str,
    internal: bool,
    error_stage: str | None,
) -> None:
    from flo.services import get_services

    display_message = (
        f"Unexpected error: {message or 'internal error'}" if internal else message
    )
    emit_error(
        get_services(verbose=False),
        display_message,
        error_kind="internal" if internal else "domain",
        error_stage=error_stage or "console_main",
        exit_code=rc,
        internal=internal,
        command="console_main",
    )
