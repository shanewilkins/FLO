"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ._artifact import RenderArtifact
from ._backend_selector import render_with_selected_backend
from .options import RenderOptions


def render_artifact(
    ir: Any, options: RenderOptions | dict | None = None
) -> RenderArtifact:
    """Render a backend-neutral artifact from canonical IR.

    Callers should depend on this artifact contract rather than any historical
    backend-specific projection. Diagram renderers now emit direct SVG artifacts.
    """
    artifact, _contract = render_artifact_and_contract(ir, options=options)
    return artifact


def render_artifact_and_contract(
    ir: Any, options: RenderOptions | dict | None = None
) -> tuple[RenderArtifact, None]:
    """Render an artifact and return no backend postprocess contract."""
    render_options = _coerce_render_options(options)
    return render_with_selected_backend(ir, render_options)


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
    "render_artifact",
    "render_artifact_and_contract",
    "RenderArtifact",
    "RenderOptions",
]
