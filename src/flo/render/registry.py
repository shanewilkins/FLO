"""Single source of truth for maintained renderer registration and dispatch."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol

from ._artifact import RenderArtifact
from ._execution import GeometryObserver, SceneObserver
from .layout_core.trace import LayoutObserver
from .options import RenderOptions
from .spaghetti import render_spaghetti_svg_artifact
from .sppm.layout_options import prepare_sppm_layout
from .sppm.renderer import render_sppm_svg_artifact
from .swimlane import render_swimlane_svg_artifact
from .value_stream import render_value_stream_svg_artifact


class RendererCallable(Protocol):
    """Registered renderer with optional observation of engine stages."""

    def __call__(
        self,
        process: Any,
        options: RenderOptions,
        *,
        layout_observer: LayoutObserver | None = None,
        geometry_observer: GeometryObserver | None = None,
        scene_observer: SceneObserver | None = None,
    ) -> tuple[RenderArtifact, None]:
        """Render through the diagram-owned production sequence."""
        ...


def _unchanged_options(options: RenderOptions) -> RenderOptions:
    return options


@dataclass(frozen=True)
class RendererRegistration:
    """One maintained diagram/backend renderer registration."""

    diagram: str
    backend: str
    render: RendererCallable
    note: str = "Direct SVG renderer is supported."
    prepare: Callable[[RenderOptions], RenderOptions] = _unchanged_options


_REGISTRATIONS = (
    RendererRegistration("swimlane", "svg", render_swimlane_svg_artifact),
    RendererRegistration("spaghetti", "svg", render_spaghetti_svg_artifact),
    RendererRegistration(
        "sppm", "svg", render_sppm_svg_artifact, prepare=prepare_sppm_layout
    ),
    RendererRegistration("value_stream", "svg", render_value_stream_svg_artifact),
)

RENDERER_REGISTRY: Mapping[tuple[str, str], RendererRegistration] = MappingProxyType(
    {
        (registration.diagram, registration.backend): registration
        for registration in _REGISTRATIONS
    }
)


def render_registered(
    ir: Any,
    render_options: RenderOptions,
    *,
    layout_observer: LayoutObserver | None = None,
    geometry_observer: GeometryObserver | None = None,
    scene_observer: SceneObserver | None = None,
) -> tuple[RenderArtifact, None]:
    """Dispatch to the exactly registered diagram/backend implementation."""
    key = (str(render_options.diagram), str(render_options.backend))
    registration = RENDERER_REGISTRY.get(key)
    if registration is None:
        raise ValueError(
            f"Unsupported render backend '{key[1]}' for diagram '{key[0]}'"
        )
    if (
        layout_observer is not None
        or geometry_observer is not None
        or scene_observer is not None
    ):
        return registration.render(
            ir,
            render_options,
            layout_observer=layout_observer,
            geometry_observer=geometry_observer,
            scene_observer=scene_observer,
        )
    return registration.render(ir, render_options)


def capability_matrix() -> dict[str, dict[str, dict[str, object]]]:
    """Build the public capability matrix from executable registrations."""
    matrix: dict[str, dict[str, dict[str, object]]] = {}
    for registration in _REGISTRATIONS:
        matrix.setdefault(registration.diagram, {})[registration.backend] = {
            "supported": True,
            "note": registration.note,
        }
    return matrix


def prepare_render_options(options: RenderOptions) -> RenderOptions:
    """Delegate diagram-owned option preparation through the executable registry."""
    registration = RENDERER_REGISTRY.get((str(options.diagram), str(options.backend)))
    return registration.prepare(options) if registration else options
