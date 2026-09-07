"""Click commands for validation and static model inspection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import click


def register_model_commands(
    cli: click.Group, execute_request: Callable[[Any], int]
) -> tuple[click.Command, click.Command]:
    """Register model commands and return their Click command objects."""

    @cli.command("validate")
    @click.argument("path", required=False)
    @click.option(
        "--format",
        "diagnostic_format",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
        help="Diagnostic output format.",
    )
    @click.option("-v", "--verbose", is_flag=True, help="Verbose output")
    def validate_cmd(
        path: str | None, diagnostic_format: str, verbose: bool
    ) -> None:  # pragma: no cover - integration
        """Validate FLO input and return non-zero on parse/validation errors."""
        from flo.app._cli_contract import CLIExecutionRequest

        rc = execute_request(
            CLIExecutionRequest(
                path=path,
                command="validate",
                options={"diagnostic_format": diagnostic_format, "verbose": verbose},
            )
        )
        raise SystemExit(rc)

    @cli.command("inspect")
    @click.argument("path", required=False)
    @click.option(
        "--analysis",
        type=click.Choice(["timing", "structure", "model"]),
        default="timing",
        show_default=True,
        help="Static analysis to run.",
    )
    @click.option(
        "--for-analysis",
        type=click.Choice(["timing", "structure"]),
        help="Report readiness for this analysis when --analysis model is selected.",
    )
    @click.option(
        "--for-diagram",
        type=click.Choice(["sppm", "swimlane", "spaghetti", "value_stream"]),
        help="Report readiness for this diagram when --analysis model is selected.",
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
        path: str | None,
        analysis: str,
        for_analysis: str | None,
        for_diagram: str | None,
        output_format: str,
        verbose: bool,
        output: str | None,
    ) -> None:  # pragma: no cover - integration
        """Inspect validated FLO input with deterministic static analysis."""
        from flo.app._cli_contract import CLIExecutionRequest

        rc = execute_request(
            CLIExecutionRequest(
                path=path,
                command="inspect",
                options={
                    "analysis": analysis,
                    "for_analysis": for_analysis,
                    "for_diagram": for_diagram,
                    "format": output_format,
                    "verbose": verbose,
                    "output": output,
                },
            )
        )
        raise SystemExit(rc)

    return validate_cmd, inspect_cmd
