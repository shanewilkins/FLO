"""Renderers package: emit presentation artifacts from canonical IR."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ._artifact import RenderArtifact
from ._execution import FinalScene, RenderExecution, RoutedGeometry
from ._geometry import resolve_svg_geometry
from ._publication import resolve_publication_page_format
from .diagnostics import attach_operation_diagnostics
from .layout_core.trace import ElkLayoutTrace
from .options import RenderOptions
from .registry import prepare_render_options, render_registered
from .themes import BUILTIN_THEMES, RenderTheme, ThemeRole


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
    return render_execution(ir, options).artifact, None


def render_execution(
    ir: Any,
    options: RenderOptions | dict | None = None,
    *,
    capture_layout: bool = False,
) -> RenderExecution:
    """Run the production sequence, optionally retaining detached engine stages.

    Stage capture observes the same execution used by ordinary artifact rendering.
    Engine results are intermediate geometry, not the finalized scene contract.
    """
    render_options = prepare_render_options(_coerce_render_options(options))
    stages: list[ElkLayoutTrace] = []
    geometry: list[RoutedGeometry] = []
    scenes: list[FinalScene] = []
    if capture_layout:
        artifact, _ = render_registered(
            ir,
            render_options,
            layout_observer=stages.append,
            geometry_observer=geometry.append,
            scene_observer=scenes.append,
        )
    else:
        artifact, _ = render_registered(ir, render_options)
    return RenderExecution(
        artifact=attach_operation_diagnostics(
            resolve_svg_geometry(artifact, render_options),
            ir,
            diagram=render_options.diagram,
            strict=render_options.layout_fit == "fit-strict",
        ),
        options=render_options,
        layout_stages=tuple(stages),
        geometry_stages=tuple(geometry),
        scene_stages=tuple(scenes),
    )


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
    "BUILTIN_THEMES",
    "RenderArtifact",
    "RenderExecution",
    "RenderOptions",
    "RenderTheme",
    "ThemeRole",
    "render_artifact",
    "render_artifact_and_contract",
    "render_execution",
    "resolve_publication_page_format",
]
