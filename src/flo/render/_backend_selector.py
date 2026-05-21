"""Explicit render backend selection for the migration period."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ._artifact import RenderArtifact
from ._graphviz_dot_sppm import _render_sppm_graph
from ._svg_flowchart import render_flowchart_svg_artifact
from ._svg_spaghetti import render_spaghetti_svg_artifact
from .graphviz_backend import (
    render_flowchart_dot,
    render_spaghetti_dot,
    render_sppm_dot,
    render_swimlane_dot,
)
from .options import RenderOptions

if TYPE_CHECKING:
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract

_ArtifactRenderer = Callable[[Any, RenderOptions], tuple[RenderArtifact, Any]]


def render_with_selected_backend(
    ir: Any, render_options: RenderOptions
) -> tuple[RenderArtifact, SppmSvgPostprocessContract | None]:
    """Render with the explicit backend selected by render options."""
    renderer = _select_artifact_renderer(render_options)
    return renderer(ir, render_options)


def _select_artifact_renderer(render_options: RenderOptions) -> _ArtifactRenderer:
    backend = str(render_options.backend or "graphviz")
    diagram = str(render_options.diagram or "flowchart")

    if backend == "svg" and diagram == "flowchart":
        return render_flowchart_svg_artifact
    if backend == "svg" and diagram == "spaghetti":
        return render_spaghetti_svg_artifact
    if backend == "graphviz":
        return _graphviz_artifact_renderer

    raise ValueError(f"Unsupported render backend '{backend}' for diagram '{diagram}'")


_GRAPHVIZ_RENDERERS = {
    "flowchart": render_flowchart_dot,
    "swimlane": render_swimlane_dot,
    "spaghetti": render_spaghetti_dot,
    "sppm": render_sppm_dot,
}


def _graphviz_artifact_renderer(
    ir: Any, render_options: RenderOptions
) -> tuple[RenderArtifact, SppmSvgPostprocessContract | None]:
    if render_options.diagram == "sppm":
        dot, contract = _render_sppm_graph(ir, render_options)
        return RenderArtifact(kind="dot", content=dot, backend="graphviz"), contract

    renderer = _GRAPHVIZ_RENDERERS.get(render_options.diagram, render_flowchart_dot)
    dot = renderer(ir, options=render_options)
    return RenderArtifact(kind="dot", content=dot, backend="graphviz"), None
