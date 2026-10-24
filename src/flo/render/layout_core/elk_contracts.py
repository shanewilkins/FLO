"""Public ELK request contracts for FLO layout-core."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from .models import LayoutResult
from .rework_semantics import ReworkRouteVariant

ElkDirection = Literal["RIGHT", "DOWN"]


@dataclass(frozen=True)
class ElkLayoutLane:
    """One lane/grouping hint in an ELK-friendly request."""

    id: str
    label: str
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class ElkLayoutNode:
    """One node prepared for layout."""

    id: str
    label: str
    kind: str
    width_px: int
    height_px: int
    lane_id: str | None = None
    partition_index: int | None = None


@dataclass(frozen=True)
class ElkLayoutEdge:
    """One directed edge prepared for layout."""

    id: str
    source_id: str
    target_id: str
    label: str | None = None
    is_rework: bool = False
    rework_variant: ReworkRouteVariant | None = None
    callout_lines: tuple[str, ...] = ()
    callout_near_source: bool = False
    outgoing_token: str | None = None
    incoming_token: str | None = None
    source_port_side: str | None = None
    target_port_side: str | None = None


@dataclass(frozen=True)
class ElkSerialization:
    """Explicit engine settings supplied by a diagram request builder."""

    root_options: dict[str, str] = field(default_factory=dict)
    lane_options: dict[str, str] = field(default_factory=dict)
    node_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    edge_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    unlabeled_edge_ids: frozenset[str] = frozenset()
    auxiliary_nodes: tuple[dict[str, Any], ...] = ()
    auxiliary_edges: tuple[dict[str, Any], ...] = ()
    constrain_terminal_layers: bool = True


@dataclass(frozen=True)
class ElkLayoutRequest:
    """Stable FLO-owned request contract for an ELK layout pass."""

    diagram: str
    direction: ElkDirection
    lanes: tuple[ElkLayoutLane, ...]
    nodes: tuple[ElkLayoutNode, ...]
    edges: tuple[ElkLayoutEdge, ...]
    strict_diagnostics: bool = False

    serialization: ElkSerialization = field(default_factory=ElkSerialization)
    result_transform: (
        Callable[[ElkLayoutRequest, LayoutResult], LayoutResult] | None
    ) = field(default=None, repr=False, compare=False)
