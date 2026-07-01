"""Option validation for FLO's run pipeline.

Validates that CLI-supplied options are internally consistent before
handing off to the render or export stage.  Raises ``CLIError`` on
any invalid combination so the caller gets a clean, actionable message.
"""

from __future__ import annotations

from flo.core.render_option_schema import render_option_keys
from flo.render._publication import resolve_publication_page_format
from flo.render.options import parse_dimension
from flo.services.errors import CLIError, EXIT_USAGE


def validate_sppm_numeric_render_options(options: dict | None) -> None:
    """Raise ``CLIError`` if any SPPM numeric option is invalid."""
    opts = options or {}
    if (
        "layout_max_width_px" in opts
        and parse_dimension(opts.get("layout_max_width_px")) is None
    ):
        raise CLIError(
            "Invalid value for --layout-max-width-px: expected a positive dimension using px, in, or cm.",
            code=EXIT_USAGE,
        )
    if "publication_page_format" in opts:
        try:
            resolve_publication_page_format(
                str(opts.get("publication_page_format") or "")
            )
        except ValueError as exc:
            raise CLIError(str(exc), code=EXIT_USAGE) from exc

    numeric_flags = (
        "layout_target_columns",
        "sppm_max_label_step_name",
        "sppm_max_label_workers",
        "sppm_max_label_ctwt",
    )

    for flag in numeric_flags:
        if flag not in opts:
            continue
        raw_value = opts.get(flag)
        if raw_value is None:
            parsed = 0
            if parsed <= 0:
                cli_flag = f"--{flag.replace('_', '-')}"
                raise CLIError(
                    f"Invalid value for {cli_flag}: expected a positive integer.",
                    code=EXIT_USAGE,
                )
            continue
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
    if output_format == "dot":
        return

    opts = options or {}
    invalid = [
        flag for flag in render_option_keys(include_render_to=True) if flag in opts
    ]
    if invalid:
        names = ", ".join(f"--{name}" for name in invalid)
        raise CLIError(
            f"Render options {names} require a diagram render output. Use --export svg, use --export dot (deprecated compatibility-only), or remove those flags.",
            code=EXIT_USAGE,
        )
