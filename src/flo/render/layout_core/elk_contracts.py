"""Public ELK request contracts for FLO layout-core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from flo.render._sppm_rework_semantics import SppmReworkVariant

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
    rework_variant: SppmReworkVariant | None = None
    callout_lines: tuple[str, ...] = ()
    callout_near_source: bool = False
    outgoing_token: str | None = None
    incoming_token: str | None = None
    source_port_side: str | None = None
    target_port_side: str | None = None


@dataclass(frozen=True)
class ElkLayoutRequest:
    """Stable FLO-owned request contract for an ELK layout pass."""

    diagram: str
    direction: ElkDirection
    lanes: tuple[ElkLayoutLane, ...]
    nodes: tuple[ElkLayoutNode, ...]
    edges: tuple[ElkLayoutEdge, ...]
    strict_diagnostics: bool = False
