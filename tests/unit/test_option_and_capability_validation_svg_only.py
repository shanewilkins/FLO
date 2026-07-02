import pytest

from flo.core._capability_validation import ensure_render_projection_supported
from flo.core._option_validation import (
    ensure_render_options_compatible_with_output,
    validate_sppm_numeric_render_options,
)
from flo.services.errors import CLIError


class _RenderOptionsLike:
    def __init__(self, *, diagram: str, backend: str) -> None:
        self.diagram = diagram
        self.backend = backend


def test_capability_validation_rejects_unknown_backend_for_supported_diagram():
    with pytest.raises(CLIError, match="Unsupported render backend"):
        ensure_render_projection_supported(
            _RenderOptionsLike(diagram="flowchart", backend="bogus")
        )


def test_capability_validation_rejects_unknown_diagram():
    with pytest.raises(CLIError, match="Unsupported diagram"):
        ensure_render_projection_supported(
            _RenderOptionsLike(diagram="bogus", backend="svg")
        )


def test_ensure_render_options_compatible_with_output_allows_svg_render_output():
    ensure_render_options_compatible_with_output(
        {
            "diagram": "flowchart",
            "orientation": "tb",
            "show_notes": True,
            "render_to": "out.svg",
        },
        "svg",
    )


def test_ensure_render_options_compatible_with_output_rejects_json_with_render_flags():
    with pytest.raises(CLIError, match="require a diagram render output"):
        ensure_render_options_compatible_with_output(
            {"diagram": "flowchart", "orientation": "tb"},
            "json",
        )


@pytest.mark.parametrize(
    "options, expected",
    [
        ({"layout_max_width_px": "0cm"}, "layout-max-width-px"),
        ({"publication_page_format": "unknown"}, "Unsupported publication_page_format"),
        ({"layout_target_columns": 0}, "layout-target-columns"),
        ({"sppm_max_label_workers": "x"}, "sppm-max-label-workers"),
        ({"sppm_max_label_ctwt": None}, "sppm-max-label-ctwt"),
    ],
)
def test_validate_sppm_numeric_render_options_rejects_invalid_values(options, expected):
    with pytest.raises(CLIError, match=expected):
        validate_sppm_numeric_render_options(options)


def test_validate_sppm_numeric_render_options_accepts_valid_values():
    validate_sppm_numeric_render_options(
        {
            "layout_max_width_px": "8.5in",
            "publication_page_format": "letter",
            "layout_target_columns": 4,
            "sppm_max_label_step_name": 24,
            "sppm_max_label_workers": 16,
            "sppm_max_label_ctwt": 12,
        }
    )
