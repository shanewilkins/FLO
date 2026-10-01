"""Option validation for FLO's run pipeline.

Validates that CLI-supplied options are internally consistent before
handing off to the render or export stage.  Raises ``CLIError`` on
any invalid combination so the caller gets a clean, actionable message.
"""

from __future__ import annotations

from flo.app.render_option_schema import render_option_keys
from flo.errors import EXIT_USAGE, CLIError
from flo.render import resolve_publication_page_format
from flo.render.options import parse_dimension


def validate_sppm_numeric_render_options(options: dict | None) -> None:
    """Raise ``CLIError`` if any SPPM numeric option is invalid."""
    opts = options or {}
    _validate_dimensions(opts)
    _validate_page_format(opts)
    _validate_positive_integer_options(opts)


def _validate_dimensions(options: dict) -> None:
    for option_name in ("layout_max_width_px", "layout_width", "layout_height"):
        if option_name in options and parse_dimension(options.get(option_name)) is None:
            cli_flag = f"--{option_name.replace('_', '-')}"
            raise CLIError(
                f"Invalid value for {cli_flag}: expected a positive dimension using px, in, cm, or mm.",
                code=EXIT_USAGE,
            )


def _validate_page_format(options: dict) -> None:
    if "publication_page_format" not in options:
        return
    try:
        resolve_publication_page_format(
            str(options.get("publication_page_format") or "")
        )
    except ValueError as exc:
        raise CLIError(str(exc), code=EXIT_USAGE) from exc


def _validate_positive_integer_options(options: dict) -> None:
    numeric_flags = (
        "layout_target_columns",
        "sppm_max_label_step_name",
        "sppm_max_label_workers",
        "sppm_max_label_ctwt",
    )

    for flag in numeric_flags:
        if flag not in options:
            continue
        raw_value = options.get(flag)
        if raw_value is None:
            parsed = 0
        else:
            try:
                parsed = int(raw_value)
            except TypeError, ValueError:
                parsed = 0
        if parsed <= 0:
            cli_flag = f"--{flag.replace('_', '-')}"
            raise CLIError(
                f"Invalid value for {cli_flag}: expected a positive integer.",
                code=EXIT_USAGE,
            )


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
