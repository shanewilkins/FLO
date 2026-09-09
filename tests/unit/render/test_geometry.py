import pytest

from flo.errors import RenderError
from flo.render._artifact import RenderArtifact
from flo.render._geometry import resolve_svg_geometry
from flo.render.options import RenderOptions


def _artifact() -> RenderArtifact:
    return RenderArtifact(
        kind="svg",
        backend="svg",
        content='<svg width="720" height="480" viewBox="0 0 720 480"></svg>',
    )


def test_geometry_metadata_records_natural_and_requested_bounds():
    artifact = resolve_svg_geometry(
        _artifact(),
        RenderOptions.from_mapping({"layout_width": "8in", "layout_height": "6in"}),
    )

    assert artifact.metadata["geometry"] == {
        "natural_width_px": 720,
        "natural_height_px": 480,
        "requested_width_px": 768,
        "requested_height_px": 576,
        "overflow_policy": "safe-fit",
        "overflows_requested_bounds": False,
        "final_width_px": 768,
        "final_height_px": 576,
        "expanded": False,
        "scale": 768 / 720,
    }
    assert (
        '<svg preserveAspectRatio="xMidYMid meet" width="768" height="576" '
        'viewBox="0 0 720 480"'
    ) in artifact.content


def test_exact_bounds_error_on_overflow_without_returning_an_artifact():
    with pytest.raises(RenderError, match="exceeds requested bounds 600x400px"):
        resolve_svg_geometry(
            _artifact(),
            RenderOptions.from_mapping(
                {
                    "layout_width": "600px",
                    "layout_height": "400px",
                    "layout_overflow": "error",
                }
            ),
        )


@pytest.mark.parametrize(
    ("options", "root_geometry", "final_geometry"),
    [
        (
            {"layout_width": "600px", "layout_overflow": "expand"},
            'width="720" height="480" viewBox="0 0 720 480"',
            (720, 480),
        ),
        (
            {"layout_height": "400px", "layout_overflow": "expand"},
            'width="720" height="480" viewBox="0 0 720 480"',
            (720, 480),
        ),
        (
            {
                "layout_width": "600px",
                "layout_height": "576px",
                "layout_overflow": "expand",
            },
            'width="720" height="576" viewBox="0 0 720 576"',
            (720, 576),
        ),
    ],
)
def test_expand_preserves_natural_coordinates_and_enlarges_only_needed_bounds(
    options: dict[str, str], root_geometry: str, final_geometry: tuple[int, int]
):
    artifact = resolve_svg_geometry(_artifact(), RenderOptions.from_mapping(options))

    assert root_geometry in artifact.content
    assert artifact.metadata["geometry"]["final_width_px"] == final_geometry[0]
    assert artifact.metadata["geometry"]["final_height_px"] == final_geometry[1]
    assert artifact.metadata["geometry"]["expanded"] is (final_geometry != (720, 480))


@pytest.mark.parametrize(
    ("options", "width", "height", "scale"),
    [
        (
            {
                "layout_width": "600px",
                "layout_height": "400px",
                "layout_overflow": "scale",
            },
            600,
            400,
            600 / 720,
        ),
        (
            {"layout_width": "600px", "layout_overflow": "scale"},
            600,
            400,
            600 / 720,
        ),
        (
            {"layout_height": "240px", "layout_overflow": "scale"},
            360,
            240,
            0.5,
        ),
    ],
)
def test_scale_only_shrinks_and_preserves_natural_viewbox(
    options: dict[str, str], width: int, height: int, scale: float
):
    artifact = resolve_svg_geometry(_artifact(), RenderOptions.from_mapping(options))

    assert f'width="{width}"' in artifact.content
    assert f'height="{height}"' in artifact.content
    assert 'viewBox="0 0 720 480"' in artifact.content
    assert 'preserveAspectRatio="xMidYMid meet"' in artifact.content
    assert artifact.metadata["geometry"]["scale"] == pytest.approx(scale)
    assert artifact.metadata["geometry"]["expanded"] is False


def test_requested_exact_canvas_is_written_when_natural_diagram_is_smaller():
    artifact = resolve_svg_geometry(
        _artifact(),
        RenderOptions.from_mapping(
            {
                "layout_width": "1000px",
                "layout_height": "800px",
                "layout_overflow": "scale",
            }
        ),
    )

    assert 'width="1000" height="800" viewBox="0 0 720 480"' in artifact.content
    assert 'preserveAspectRatio="xMidYMid meet"' in artifact.content
    assert artifact.metadata["geometry"]["scale"] == pytest.approx(1000 / 720)


def test_safe_fit_rejects_scaling_below_the_legibility_floor():
    with pytest.raises(RenderError, match=r"below the safe readability floor 0\.75"):
        resolve_svg_geometry(
            _artifact(),
            RenderOptions.from_mapping(
                {"layout_width": "400px", "layout_height": "240px"}
            ),
        )
