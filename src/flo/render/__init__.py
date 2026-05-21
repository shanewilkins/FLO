"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from ._artifact import RenderArtifact
from ._backend_selector import render_with_selected_backend
from .graphviz_backend import (
    render_flowchart_dot,
    render_spaghetti_dot,
    render_sppm_dot,
    render_swimlane_dot,
)
from .options import RenderOptions

if TYPE_CHECKING:
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract


def render_artifact(
    ir: Any, options: RenderOptions | dict | None = None
) -> RenderArtifact:
    """Render a backend-neutral artifact from canonical IR.

    Callers should depend on this artifact contract rather than assuming DOT is
    the only meaningful render product. Some diagram families still lower
    through Graphviz, while migrated slices may emit direct SVG artifacts.
    """
    artifact, _contract = render_artifact_and_contract(ir, options=options)
    return artifact


def render_artifact_and_contract(
    ir: Any, options: RenderOptions | dict | None = None
) -> tuple[RenderArtifact, SppmSvgPostprocessContract | None]:
    """Render an artifact and return any backend-specific postprocess contract."""
    render_options = _coerce_render_options(options)
    return render_with_selected_backend(ir, render_options)


def render_dot(ir: Any, options: RenderOptions | dict | None = None) -> str:
    """Legacy compatibility wrapper that forces Graphviz DOT output."""
    render_options = _coerce_render_options(options, force_backend="graphviz")
    artifact, _contract = render_with_selected_backend(ir, render_options)
    return artifact.content


def render_dot_and_contract(
    ir: Any, options: RenderOptions | dict | None = None
) -> tuple[str, SppmSvgPostprocessContract | None]:
    """Legacy compatibility wrapper for Graphviz DOT plus postprocess contract.

    For non-SPPM diagrams the contract is ``None``.  Use this instead of
    ``render_dot`` when the caller needs to pass the contract to the SVG
    postprocessor (e.g. ``render_dot_to_file``).
    """
    render_options = _coerce_render_options(options, force_backend="graphviz")
    artifact, contract = render_with_selected_backend(ir, render_options)
    return artifact.content, contract


def _coerce_render_options(
    options: RenderOptions | dict | None, force_backend: str | None = None
) -> RenderOptions:
    render_options = (
        options
        if isinstance(options, RenderOptions)
        else RenderOptions.from_mapping(options)
    )
    if force_backend is None or render_options.backend == force_backend:
        return render_options
    return replace(render_options, backend=force_backend)


__all__ = [
    "render_flowchart_dot",
    "render_swimlane_dot",
    "render_spaghetti_dot",
    "render_sppm_dot",
    "render_artifact",
    "render_artifact_and_contract",
    "RenderArtifact",
    "render_dot",
    "render_dot_and_contract",
    "RenderOptions",
]
