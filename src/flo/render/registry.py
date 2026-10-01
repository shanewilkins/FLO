"""Single source of truth for maintained renderer registration and dispatch."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from ._artifact import RenderArtifact
from .options import RenderOptions
from .spaghetti import render_spaghetti_svg_artifact
from .sppm.renderer import render_sppm_svg_artifact
from .swimlane import render_swimlane_svg_artifact
from .value_stream import render_value_stream_svg_artifact

RendererCallable = Callable[[Any, RenderOptions], tuple[RenderArtifact, None]]


@dataclass(frozen=True)
class RendererRegistration:
    """One maintained diagram/backend renderer registration."""

    diagram: str
    backend: str
    render: RendererCallable
    note: str = "Direct SVG renderer is supported."


_REGISTRATIONS = (
    RendererRegistration("swimlane", "svg", render_swimlane_svg_artifact),
    RendererRegistration("spaghetti", "svg", render_spaghetti_svg_artifact),
    RendererRegistration("sppm", "svg", render_sppm_svg_artifact),
    RendererRegistration("value_stream", "svg", render_value_stream_svg_artifact),
)

RENDERER_REGISTRY: Mapping[tuple[str, str], RendererRegistration] = MappingProxyType(
    {
        (registration.diagram, registration.backend): registration
        for registration in _REGISTRATIONS
    }
)


def render_registered(
    ir: Any, render_options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Dispatch to the exactly registered diagram/backend implementation."""
    key = (str(render_options.diagram), str(render_options.backend))
    registration = RENDERER_REGISTRY.get(key)
    if registration is None:
        raise ValueError(
            f"Unsupported render backend '{key[1]}' for diagram '{key[0]}'"
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
