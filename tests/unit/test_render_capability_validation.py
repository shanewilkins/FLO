from flo.core._capability_validation import ensure_render_projection_supported
from flo.render.capability_matrix import (
    RENDER_CAPABILITY_MATRIX,
    supported_backends_for_diagram,
)
from flo.render.options import RenderOptions
from flo.services.errors import CLIError


def test_render_capability_matrix_covers_known_diagrams() -> None:
    assert set(RENDER_CAPABILITY_MATRIX.keys()) == {
        "flowchart",
        "swimlane",
        "spaghetti",
        "sppm",
    }


def test_supported_backends_for_swimlane_excludes_svg() -> None:
    assert supported_backends_for_diagram("swimlane") == ("graphviz",)


def test_projection_validator_accepts_supported_pair() -> None:
    ensure_render_projection_supported(RenderOptions(diagram="sppm", backend="svg"))


def test_projection_validator_rejects_swimlane_svg() -> None:
    try:
        ensure_render_projection_supported(
            RenderOptions(diagram="swimlane", backend="svg")
        )
    except CLIError as exc:
        message = str(exc)
        assert "Unsupported projection" in message
        assert "diagram 'swimlane'" in message
        assert "backend 'svg'" in message
        assert "Supported backends: graphviz" in message
        return

    raise AssertionError("Expected CLIError for unsupported swimlane+svg")
