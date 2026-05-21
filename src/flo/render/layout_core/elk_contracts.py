"""Public ELK request contracts for FLO layout-core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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


@dataclass(frozen=True)
class ElkLayoutEdge:
    """One directed edge prepared for layout."""

    id: str
    source_id: str
    target_id: str
    label: str | None = None


@dataclass(frozen=True)
class ElkLayoutRequest:
    """Stable FLO-owned request contract for an ELK layout pass."""

    diagram: str
    direction: ElkDirection
    lanes: tuple[ElkLayoutLane, ...]
    nodes: tuple[ElkLayoutNode, ...]
    edges: tuple[ElkLayoutEdge, ...]
