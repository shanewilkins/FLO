"""Explicit SVG renderer selection."""

from __future__ import annotations

from typing import Any, Callable

from ._artifact import RenderArtifact
from ._svg_flowchart import render_flowchart_svg_artifact
from ._svg_sppm import render_sppm_svg_artifact
from ._svg_spaghetti import render_spaghetti_svg_artifact
from ._svg_swimlane import render_swimlane_svg_artifact
from .options import RenderOptions

_ArtifactRenderer = Callable[[Any, RenderOptions], tuple[RenderArtifact, Any]]


def render_with_selected_backend(
    ir: Any, render_options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render with the selected SVG renderer."""
    renderer = _select_artifact_renderer(render_options)
    return renderer(ir, render_options)


def _select_artifact_renderer(render_options: RenderOptions) -> _ArtifactRenderer:
    backend = str(render_options.backend or "svg")
    diagram = str(render_options.diagram or "flowchart")

    if backend == "svg" and diagram == "flowchart":
        return render_flowchart_svg_artifact
    if backend == "svg" and diagram == "swimlane":
        return render_swimlane_svg_artifact
    if backend == "svg" and diagram == "spaghetti":
        return render_spaghetti_svg_artifact
    if backend == "svg" and diagram == "sppm":
        return render_sppm_svg_artifact

    raise ValueError(f"Unsupported render backend '{backend}' for diagram '{diagram}'")
