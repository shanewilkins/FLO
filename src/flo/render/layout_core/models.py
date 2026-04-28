"""Data contracts for the renderer-agnostic placement core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AlignMode = Literal["start", "center", "end"]
OrientationMode = Literal["lr", "tb"]


@dataclass(frozen=True)
class NodeMeasure:
    """Physical dimensions and identity for a single node."""

    id: str
    width_px: int
    height_px: int
    kind: str = ""


@dataclass(frozen=True)
class PlacementConstraints:
    """Policy inputs that drive packing and alignment decisions."""

    orientation: OrientationMode = "lr"
    max_width_px: int | None = None
    max_height_px: int | None = None
    gap_major: int = 20
    gap_minor: int = 40
    margin: int = 20
    align_line: AlignMode = "start"
    align_stack: AlignMode = "start"


@dataclass(frozen=True)
class LinePlacement:
    """Geometry for one packed line (row for LR, column for TB)."""

    line_index: int
    node_ids: tuple[str, ...]
    node_major_offsets: tuple[int, ...]
    node_cross_offsets: tuple[int, ...]
    major_size: int
    cross_offset: int
    cross_size: int


@dataclass(frozen=True)
class PlacementPlan:
    """Complete renderer-agnostic placement output for a set of nodes."""

    lines: tuple[LinePlacement, ...]
    node_line_index: dict[str, int]
    boundary_edges: frozenset[tuple[str, str]]
    total_major: int
    total_cross: int
    orientation: OrientationMode
