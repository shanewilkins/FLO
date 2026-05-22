"""Data contracts for the renderer-agnostic placement core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from flo.render._sppm_rework_semantics import SppmReworkVariant

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


@dataclass(frozen=True)
class LayoutPoint:
    """One routed or positioned point in final diagram geometry."""

    x_px: float
    y_px: float


@dataclass(frozen=True)
class LayoutBounds:
    """Final positioned bounds for one diagram object."""

    x_px: float
    y_px: float
    width_px: float
    height_px: float


@dataclass(frozen=True)
class LayoutLaneFrame:
    """Final frame assigned to one lane or band grouping."""

    id: str
    label: str
    bounds: LayoutBounds
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class RoutedEdgePath:
    """Final routed geometry for one logical edge."""

    edge: tuple[str, str]
    points: tuple[LayoutPoint, ...]
    label: str | None = None
    label_point: LayoutPoint | None = None
    source_port_side: str | None = None
    target_port_side: str | None = None
    is_rework: bool = False
    rework_variant: SppmReworkVariant | None = None
    callout_lines: tuple[str, ...] = ()
    callout_near_source: bool = False
    outgoing_token: str | None = None
    incoming_token: str | None = None


@dataclass(frozen=True)
class LayoutResult:
    """Backend-neutral final geometry emitted by a layout engine."""

    orientation: OrientationMode
    canvas_bounds: LayoutBounds
    node_bounds: dict[str, LayoutBounds]
    edge_paths: dict[tuple[str, str], RoutedEdgePath]
    lanes: tuple[LayoutLaneFrame, ...] = ()

    def bounds_for(self, node_id: str) -> LayoutBounds | None:
        """Return final bounds for a node ID, if present."""
        return self.node_bounds.get(node_id)

    def path_for(self, source: str, target: str) -> RoutedEdgePath | None:
        """Return final routed geometry for a logical edge, if present."""
        return self.edge_paths.get((source, target))


def serialize_layout_result(result: LayoutResult) -> str:
    """Return a stable snapshot of final layout geometry."""
    lines = [
        "canvas"
        f" x={_format_coord(result.canvas_bounds.x_px)}"
        f" y={_format_coord(result.canvas_bounds.y_px)}"
        f" w={_format_coord(result.canvas_bounds.width_px)}"
        f" h={_format_coord(result.canvas_bounds.height_px)}",
        f"orientation {result.orientation}",
    ]
    for lane in result.lanes:
        lines.append(
            "lane"
            f" {lane.id} label={lane.label}"
            f" x={_format_coord(lane.bounds.x_px)}"
            f" y={_format_coord(lane.bounds.y_px)}"
            f" w={_format_coord(lane.bounds.width_px)}"
            f" h={_format_coord(lane.bounds.height_px)}"
            f" nodes={','.join(lane.node_ids)}"
        )
    for node_id in sorted(result.node_bounds.keys()):
        bounds = result.node_bounds[node_id]
        lines.append(
            "node"
            f" {node_id}"
            f" x={_format_coord(bounds.x_px)}"
            f" y={_format_coord(bounds.y_px)}"
            f" w={_format_coord(bounds.width_px)}"
            f" h={_format_coord(bounds.height_px)}"
        )
    for edge in sorted(result.edge_paths.keys()):
        path = result.edge_paths[edge]
        source, target = edge
        point_text = " -> ".join(
            f"({_format_coord(point.x_px)},{_format_coord(point.y_px)})"
            for point in path.points
        )
        label_suffix = f" label={path.label}" if path.label else ""
        lines.append(f"edge {source}->{target}{label_suffix} points={point_text}")
    return "\n".join(lines)


def _format_coord(value: float) -> str:
    return f"{value:g}"
