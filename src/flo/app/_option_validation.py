"""Option validation for FLO's run pipeline.

Validates that CLI-supplied options are internally consistent before
handing off to the render or export stage.  Raises ``CLIError`` on
any invalid combination so the caller gets a clean, actionable message.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from flo.app.render_option_schema import render_option_keys
from flo.errors import EXIT_USAGE, CLIError
from flo.render.options import POSITIVE_INTEGER_OPTIONS, RenderInput


def validate_render_options(
    options: dict | None,
    *,
    config_file: Path | None = None,
    origins: dict[str, str] | None = None,
) -> dict:
    """Validate effective CLI/config values once and retain input provenance."""
    opts = dict(options or {})
    try:
        parsed = RenderInput.model_validate(opts)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_input=False)
        details = []
        for error in errors:
            key, *suffix = error["loc"]
            path = (origins or {}).get(str(key), str(key))
            path = ".".join((path, *(str(part) for part in suffix)))
            details.append(
                f"  {path}: Invalid value for --{str(key).replace('_', '-')}: {error['msg']}"
            )
        heading = (
            f"Invalid diagrams.toml ({config_file})"
            if config_file
            and any(error["loc"][0] in (origins or {}) for error in errors)
            else "Invalid render options"
        )
        raise CLIError(
            heading
            + ":\n"
            + "\n".join(details)
            + "\nCorrect these configuration fields and retry.",
            code=EXIT_USAGE,
            error_stage="option_validation",
        ) from exc
    return {
        **opts,
        **{
            key: getattr(parsed, key) for key in opts if key in POSITIVE_INTEGER_OPTIONS
        },
    }


def ensure_render_options_compatible_with_output(
    options: dict | None, output_format: str
) -> None:
    """Raise ``CLIError`` if diagram-render flags are used with a non-render export."""
    if output_format == "svg":
        return

    opts = options or {}
    invalid = [
        flag for flag in render_option_keys(include_render_to=True) if flag in opts
    ]
    if invalid:
        names = ", ".join(f"--{name}" for name in invalid)
        raise CLIError(
            f"Render options {names} require a diagram render output. Use --export svg or remove those flags.",
            code=EXIT_USAGE,
        )
