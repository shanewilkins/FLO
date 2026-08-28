"""Click commands for validation and static model inspection."""

from __future__ import annotations

from typing import Any, Callable, Optional

import click


def register_model_commands(
    cli: click.Group, execute_request: Callable[[Any], int]
) -> tuple[click.Command, click.Command]:
    """Register model commands and return their Click command objects."""

    @cli.command("validate")
    @click.argument("path", required=False)
    @click.option("-v", "--verbose", is_flag=True, help="Verbose output")
    def validate_cmd(
        path: Optional[str], verbose: bool
    ) -> None:  # pragma: no cover - integration
        """Validate FLO input and return non-zero on parse/validation errors."""
        from flo.core._cli_contract import CLIExecutionRequest

        rc = execute_request(
            CLIExecutionRequest(
                path=path,
                command="validate",
                options={"verbose": verbose},
            )
        )
        raise SystemExit(rc)

    @cli.command("inspect")
    @click.argument("path", required=False)
    @click.option(
        "--analysis",
        type=click.Choice(["timing"]),
        default="timing",
        show_default=True,
        help="Static analysis to run.",
    )
    @click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
        help="Report format.",
    )
    @click.option("-v", "--verbose", is_flag=True, help="Verbose output")
    @click.option("-o", "--output", help="Write output to file")
    def inspect_cmd(
        path: Optional[str],
        analysis: str,
        output_format: str,
        verbose: bool,
        output: Optional[str],
    ) -> None:  # pragma: no cover - integration
        """Inspect validated FLO input with deterministic static analysis."""
        from flo.core._cli_contract import CLIExecutionRequest

        rc = execute_request(
            CLIExecutionRequest(
                path=path,
                command="inspect",
                options={
                    "analysis": analysis,
                    "format": output_format,
                    "verbose": verbose,
                    "output": output,
                },
            )
        )
        raise SystemExit(rc)

    return validate_cmd, inspect_cmd
