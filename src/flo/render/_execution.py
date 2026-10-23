"""Observed production rendering results; engine geometry is an intermediate stage."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ._artifact import RenderArtifact
from ._diagnostics import RenderDiagnostic
from .layout_core.models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    RoutedEdgePath,
)
from .layout_core.trace import ElkLayoutTrace
from .options import RenderOptions


@dataclass(frozen=True)
class RoutedGeometry:
    """Final node/route geometry; attachments and annotations remain later stages."""

    diagram: str
    node_bounds: Mapping[str, LayoutBounds]
    edge_paths: Mapping[tuple[str, str], RoutedEdgePath]
    lanes: tuple[LayoutLaneFrame, ...]
    canvas_bounds: LayoutBounds
    node_groups: Mapping[str, frozenset[str]]
    edge_groups: Mapping[str, frozenset[tuple[str, str]]]
    diagnostics: tuple[RenderDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        """Freeze detached mappings so stage consumers cannot change geometry."""
        for name in ("node_bounds", "edge_paths", "node_groups", "edge_groups"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


GeometryObserver = Callable[[RoutedGeometry], None]


@dataclass(frozen=True)
class PositionedText:
    """One text run whose baseline and typography are resolved before emission."""

    text: str
    x: float
    y: float
    anchor: str = "middle"
    size_px: int = 12
    weight: str | None = None
    role_field: str = "title_text"


@dataclass(frozen=True)
class EdgeAnnotation:
    """A positioned label, callout, or continuation token."""

    kind: str
    bounds: LayoutBounds
    texts: tuple[PositionedText, ...]
    token: str | None = None
    token_position: str | None = None


@dataclass(frozen=True)
class AttachedEdge:
    """A fully attached connector and its already positioned annotations."""

    edge: tuple[str, str]
    points: tuple[LayoutPoint, ...]
    rework: bool
    variant: str
    annotations: tuple[EdgeAnnotation, ...] = ()


@dataclass(frozen=True)
class PositionedBand:
    """Publication band line and text positions, ready for serialization."""

    name: str
    x: float
    y: float
    width: float
    texts: tuple[PositionedText, ...]


@dataclass(frozen=True)
class FinalScene:
    """Complete local diagram geometry before artifact viewport transformation."""

    routed: RoutedGeometry
    edges: tuple[AttachedEdge, ...]
    occupied_bounds: tuple[LayoutBounds, ...]
    diagnostics: tuple[RenderDiagnostic, ...]
    width: float
    height: float
    content_origin: LayoutPoint
    page_id: str
    page_format: str | None
    header: PositionedBand | None = None
    footer: PositionedBand | None = None


SceneObserver = Callable[[FinalScene], None]


@dataclass(frozen=True)
class RenderExecution:
    """Resolved options, final artifact, and optionally captured intermediate stages."""

    artifact: RenderArtifact
    options: RenderOptions
    layout_stages: tuple[ElkLayoutTrace, ...] = ()

    geometry_stages: tuple[RoutedGeometry, ...] = ()

    scene_stages: tuple[FinalScene, ...] = ()
