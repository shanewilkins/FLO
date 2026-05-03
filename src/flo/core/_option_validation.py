"""Option validation for FLO's run pipeline.

Validates that CLI-supplied options are internally consistent before
handing off to the render or export stage.  Raises ``CLIError`` on
any invalid combination so the caller gets a clean, actionable message.
"""

from __future__ import annotations

from flo.services.errors import CLIError, EXIT_USAGE


def validate_sppm_numeric_render_options(options: dict | None) -> None:
    """Raise ``CLIError`` if any SPPM numeric option is not a positive integer."""
    opts = options or {}
    numeric_flags = (
        "layout_max_width_px",
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
        except (TypeError, ValueError):
            parsed = 0

        if parsed <= 0:
            cli_flag = f"--{flag.replace('_', '-')}"
            raise CLIError(
                f"Invalid value for {cli_flag}: expected a positive integer.",
                code=EXIT_USAGE,
            )


def ensure_render_options_compatible_with_output(options: dict | None, output_format: str) -> None:
    """Raise ``CLIError`` if render-only flags are used with a non-DOT output format."""
    if output_format == "dot":
        return

    opts = options or {}
    invalid = [
        flag
        for flag in (
            "diagram",
            "profile",
            "detail",
            "orientation",
            "show_notes",
            "subprocess_view",
            "spaghetti_channel",
            "spaghetti_people_mode",
            "sppm_theme",
            "layout_wrap",
            "layout_fit",
            "layout_spacing",
            "sppm_step_numbering",
            "sppm_label_density",
            "sppm_wrap_strategy",
            "sppm_truncation_policy",
            "layout_max_width_px",
            "layout_target_columns",
            "sppm_max_label_step_name",
            "sppm_max_label_workers",
            "sppm_max_label_ctwt",
            "sppm_output_profile",
            "render_to",
        )
        if flag in opts
    ]
    if invalid:
        names = ", ".join(f"--{name}" for name in invalid)
        raise CLIError(
            f"Render options {names} require DOT output. Use --export dot or remove those flags.",
            code=EXIT_USAGE,
        )
