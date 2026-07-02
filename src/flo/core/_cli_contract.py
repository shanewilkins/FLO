"""Framework-agnostic CLI parsing and dispatch contract.

This module defines the contract between CLI parsing (whether via Click,
argparse, or other frameworks) and the execution engine. It enables:
- Testable parsing without framework coupling
- Consistent behavior across entry points
- Reduced monkeypatch requirements in tests
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CLIExecutionRequest:
    """Typed execution request shared between parser adapters and dispatch.

    Attributes:
        path: File path or '-' for stdin (None means no explicit path).
        command: CLI command name (render, validate, export).
        options: Render/execution options dict (may be empty).
    """

    path: str | None
    command: str
    options: dict[str, Any]

    def asdict(self) -> dict[str, Any]:
        """Return as a dict for backward compatibility with older signatures."""
        return {"path": self.path, "command": self.command, "options": self.options}


# Backward-compatible alias retained for existing imports/tests.
ParsedArgs = CLIExecutionRequest


def parse_cli_args(argv: list[str] | None) -> CLIExecutionRequest:
    """Parse CLI arguments from argv into a framework-agnostic contract.

    This function is independent of Click or any other framework, making it
    directly testable and reusable across entry points.

    Args:
        argv: Command-line arguments (e.g., sys.argv[1:]). If None, returns
              a default render command with no path.

    Returns:
        CLIExecutionRequest contract ready for dispatch.

    Raises:
        SystemExit: On parsing errors (for argparse compatibility).
    """
    from flo.core.cli_args import parse_args as argparse_parse_args
    from flo.services import get_services

    if argv is None:
        return CLIExecutionRequest(path=None, command="render", options={})

    services = get_services(verbose=False)
    path, command, options, _services, _logger = argparse_parse_args(argv, services)
    return CLIExecutionRequest(path=path, command=command, options=dict(options or {}))
