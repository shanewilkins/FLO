from typing import cast

from flo.core._capability_validation import ensure_render_projection_supported
from flo.render.capability_matrix import (
    RENDER_CAPABILITY_MATRIX,
    supported_backends_for_diagram,
)
from flo.render.options import RenderOptions
from flo.render.options import DiagramType
from flo.services.errors import CLIError


def test_render_capability_matrix_covers_known_diagrams() -> None:
    assert set(RENDER_CAPABILITY_MATRIX.keys()) == {
        "flowchart",
        "swimlane",
        "spaghetti",
        "sppm",
    }


def test_supported_backends_for_swimlane_is_svg_only() -> None:
    assert supported_backends_for_diagram("swimlane") == ("svg",)


def test_projection_validator_accepts_supported_pair() -> None:
    ensure_render_projection_supported(RenderOptions(diagram="sppm", backend="svg"))


def test_projection_validator_accepts_swimlane_svg() -> None:
    ensure_render_projection_supported(RenderOptions(diagram="swimlane", backend="svg"))


def test_projection_validator_rejects_unknown_diagram() -> None:
    try:
        ensure_render_projection_supported(
            RenderOptions(diagram=cast(DiagramType, "bogus"))
        )
    except CLIError as exc:
        message = str(exc)
        assert "Unsupported diagram" in message
        return

    raise AssertionError("Expected CLIError for unsupported diagram")
