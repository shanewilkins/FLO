"""Support helpers for SPPM routing plan construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._autoformat_wrap import WrapPlan
from ._sppm_continuation_labels import build_sppm_continuation_anchor_attrs
from ._sppm_postprocess_contract import SppmSvgPostprocessContract
from ._sppm_port_policy import is_sppm_rework_edge
from .layout_core import (
    CorridorPlan,
    LinePlacement,
    PlacementPlan,
    RoutePlan,
    build_corridor_plan,
    build_route_plan,
)
from .options import RenderOptions


@dataclass(frozen=True)
class SppmRouteAnchor:
    """Invisible anchor node used to split a routed edge into segments."""

    anchor_id: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmCorridorNode:
    """Reserved corridor node metadata for future lane-aware routing."""

    node_id: str
    lane_id: str
    role: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmRouteSegment:
    """A single directed segment within a routed edge."""

    source_id: str
    target_id: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmEdgeRoute:
    """Resolved route description for one logical edge."""

    source: str
    target: str
    kind: str
    is_boundary: bool
    is_rework: bool
    lane_id: str | None
    corridor_nodes: tuple[SppmCorridorNode, ...]
    anchors: tuple[SppmRouteAnchor, ...]
    segments: tuple[SppmRouteSegment, ...]


@dataclass(frozen=True)
class SppmRoutingPlan:
    """Collection of routed SPPM edges keyed by source and target ids."""

    routes: dict[tuple[str, str], SppmEdgeRoute]
    corridor_plan: CorridorPlan
    route_plan: RoutePlan
    svg_postprocess_contract: SppmSvgPostprocessContract = SppmSvgPostprocessContract()

    def route_for(self, source: str, target: str) -> SppmEdgeRoute | None:
        """Return the resolved route for a source-target edge pair, if any."""
        return self.routes.get((source, target))


def edge_pairs(edges: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Return normalized (source, target) pairs for valid edges."""
    pairs: list[tuple[str, str]] = []
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source and target:
            pairs.append((source, target))
    return pairs


def build_corridor_metadata(
    *, placement: PlacementPlan, edge_pairs: list[tuple[str, str]]
) -> CorridorPlan:
    """Build corridor metadata, using empty metadata for single-line layouts."""
    if len(placement.lines) <= 1:
        return CorridorPlan(
            lanes=(),
            entry_anchors={},
            exit_anchors={},
            lane_occupancy={},
            edge_lane_hops={},
        )
    return build_corridor_plan(placement=placement, edges=edge_pairs)


def build_core_route_plan(
    *,
    placement: PlacementPlan,
    edge_pairs: list[tuple[str, str]],
    corridor_plan: CorridorPlan,
) -> RoutePlan:
    """Build core route plan from placement and corridor metadata."""
    return build_route_plan(
        placement=placement, corridor=corridor_plan, edges=edge_pairs
    )


def placement_for_routing(
    *,
    nodes: list[dict[str, Any]],
    options: RenderOptions,
    wrap_plan: WrapPlan,
) -> PlacementPlan:
    """Build a placement plan suitable for deterministic SPPM routing."""
    if wrap_plan.placement_plan is not None:
        return wrap_plan.placement_plan

    line_node_ids = (
        wrap_plan.chunks
        if wrap_plan.active and wrap_plan.chunks
        else [ordered_node_ids(nodes)]
    )
    lines: list[LinePlacement] = []
    node_line_index: dict[str, int] = {}
    for line_index, node_ids in enumerate(line_node_ids):
        tuple_ids = tuple(node_ids)
        lines.append(
            LinePlacement(
                line_index=line_index,
                node_ids=tuple_ids,
                node_major_offsets=tuple(0 for _ in tuple_ids),
                node_cross_offsets=tuple(0 for _ in tuple_ids),
                major_size=0,
                cross_offset=0,
                cross_size=0,
            )
        )
        for node_id in tuple_ids:
            node_line_index[node_id] = line_index

    return PlacementPlan(
        lines=tuple(lines),
        node_line_index=node_line_index,
        boundary_edges=frozenset(wrap_plan.boundary_edges),
        total_major=0,
        total_cross=0,
        orientation=options.orientation,
    )


def ordered_node_ids(nodes: list[dict[str, Any]]) -> list[str]:
    """Return node ids in input order, skipping empty ids."""
    ordered: list[str] = []
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id:
            ordered.append(node_id)
    return ordered


def node_kinds(nodes: list[dict[str, Any]]) -> dict[str, str]:
    """Return normalized node kind keyed by node id."""
    kinds: dict[str, str] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        kinds[node_id] = (
            str(node.get("kind") or node.get("type") or "task").strip().lower()
        )
    return kinds


def collect_rework_branch_metadata(
    *,
    edges: list[dict[str, Any]],
    node_kinds: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Return branch-out rework metadata keyed by rework target node id."""
    metadata_by_target: dict[str, dict[str, Any]] = {}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if not is_explicit_rework_branch_out(
            edge=edge, source_kind=node_kinds.get(source, "task")
        ):
            continue
        raw = edge.get("metadata")
        if isinstance(raw, dict) and raw:
            metadata_by_target[target] = dict(raw)
    return metadata_by_target


def collect_rework_return_sources(
    *,
    edges: list[dict[str, Any]],
    step_numbering: dict[str, int],
    node_kinds: dict[str, str],
    branch_metadata_by_rework_target: dict[str, dict[str, Any]],
) -> set[str]:
    """Return rework-source node ids that have explicit return rework edges."""
    sources: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if source not in branch_metadata_by_rework_target:
            continue
        if not is_sppm_rework_edge(
            edge=edge, step_numbering=step_numbering, source=source, target=target
        ):
            continue
        if is_explicit_rework_branch_out(
            edge=edge, source_kind=node_kinds.get(source, "task")
        ):
            continue
        sources.add(source)
    return sources


def edge_with_rework_metadata_policy(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    step_numbering: dict[str, int],
    node_kinds: dict[str, str],
    branch_metadata_by_rework_target: dict[str, dict[str, Any]],
    rework_return_sources: set[str],
) -> dict[str, Any]:
    """Return edge copy with merged/suppressed rework databox metadata policy applied."""
    effective = dict(edge)
    if not is_sppm_rework_edge(
        edge=edge, step_numbering=step_numbering, source=source, target=target
    ):
        return effective

    source_kind = node_kinds.get(source, "task")
    is_branch_out = is_explicit_rework_branch_out(edge=edge, source_kind=source_kind)
    if is_branch_out and target in rework_return_sources:
        effective["_sppm_suppress_rework_databox"] = True
        return effective

    if source in branch_metadata_by_rework_target and not is_branch_out:
        merged: dict[str, Any] = {}
        merged.update(branch_metadata_by_rework_target[source])
        raw = edge.get("metadata")
        if isinstance(raw, dict):
            merged.update(raw)
        if merged:
            effective["metadata"] = merged
    return effective


def is_explicit_rework_branch_out(*, edge: dict[str, Any], source_kind: str) -> bool:
    """Return True when edge explicitly represents outbound rework from a decision context."""
    if (
        str(edge.get("edge_type") or "").strip().lower() != "rework"
        and edge.get("rework") is not True
    ):
        return False
    return (
        source_kind == "decision"
        or edge.get("outcome") is not None
        or edge.get("label") is not None
    )


def resolve_lane_id(
    *,
    edge: tuple[str, str],
    route_plan: RoutePlan,
    boundary_lanes: dict[tuple[str, str], str],
) -> str | None:
    """Resolve the preferred lane id for an edge from boundary or core-route hops."""
    if edge in boundary_lanes:
        return boundary_lanes[edge]
    core_route = route_plan.route_for(edge[0], edge[1])
    if core_route is not None and core_route.lane_hops:
        return core_route.lane_hops[0]
    return None


def _build_lr_boundary_corridor_with_continuations(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    source_port: str,
    target_port: str,
    lane_id: str,
    exit_anchor_id: str,
    boundary_anchor_base: str,
    outgoing_token: str,
    incoming_token: str,
) -> SppmEdgeRoute:
    """Build an LR wrapped boundary route that uses continuation anchors."""
    outgoing_anchor_id = f"{boundary_anchor_base}_out"
    incoming_anchor_id = f"{boundary_anchor_base}_in"
    anchors = _build_boundary_continuation_anchors(
        outgoing_anchor_id=outgoing_anchor_id,
        incoming_anchor_id=incoming_anchor_id,
        outgoing_token=outgoing_token,
        incoming_token=incoming_token,
    )
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="corridor",
        is_boundary=True,
        is_rework=False,
        lane_id=lane_id,
        corridor_nodes=(),
        anchors=anchors,
        segments=(
            _build_route_segment(
                source_id=source,
                target_id=exit_anchor_id,
                attrs=[source_port, "arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=exit_anchor_id,
                target_id=outgoing_anchor_id,
                attrs=["arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=outgoing_anchor_id,
                target_id=incoming_anchor_id,
                attrs=["arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=incoming_anchor_id,
                target_id=target,
                attrs=[target_port, *edge_attrs],
            ),
        ),
    )


def _build_lr_boundary_corridor_direct(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    source_port: str,
    target_port: str,
    lane_id: str,
    exit_anchor_id: str,
) -> SppmEdgeRoute:
    """Build an LR wrapped boundary route without continuation anchors."""
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="corridor",
        is_boundary=True,
        is_rework=False,
        lane_id=lane_id,
        corridor_nodes=(),
        anchors=(),
        segments=(
            _build_route_segment(
                source_id=source,
                target_id=exit_anchor_id,
                attrs=[source_port, "arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=exit_anchor_id,
                target_id=target,
                attrs=[target_port, *edge_attrs],
            ),
        ),
    )


def _build_boundary_corridor_with_continuations(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    source_port: str,
    target_port: str,
    lane_id: str,
    boundary_anchor_base: str,
    outgoing_token: str,
    incoming_token: str,
) -> SppmEdgeRoute:
    """Build a boundary corridor route that uses continuation anchors."""
    outgoing_anchor_id = f"{boundary_anchor_base}_out"
    incoming_anchor_id = f"{boundary_anchor_base}_in"
    anchors = _build_boundary_continuation_anchors(
        outgoing_anchor_id=outgoing_anchor_id,
        incoming_anchor_id=incoming_anchor_id,
        outgoing_token=outgoing_token,
        incoming_token=incoming_token,
    )
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="corridor",
        is_boundary=True,
        is_rework=False,
        lane_id=lane_id,
        corridor_nodes=(),
        anchors=anchors,
        segments=(
            _build_route_segment(
                source_id=source,
                target_id=outgoing_anchor_id,
                attrs=[source_port, "arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=outgoing_anchor_id,
                target_id=incoming_anchor_id,
                attrs=["arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=incoming_anchor_id,
                target_id=target,
                attrs=[target_port, *edge_attrs],
            ),
        ),
    )


def _build_boundary_corridor_with_point_anchor(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    source_port: str,
    target_port: str,
    lane_id: str,
    anchor_id: str,
) -> SppmEdgeRoute:
    """Build a boundary corridor route that uses a single invisible point anchor."""
    anchor = SppmRouteAnchor(
        anchor_id=anchor_id,
        attrs=("shape=point", "width=0.01", "height=0.01", 'label=""', "style=invis"),
    )
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="corridor",
        is_boundary=True,
        is_rework=False,
        lane_id=lane_id,
        corridor_nodes=(),
        anchors=(anchor,),
        segments=(
            _build_route_segment(
                source_id=source,
                target_id=anchor_id,
                attrs=[source_port, "arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=anchor_id,
                target_id=target,
                attrs=[target_port, *edge_attrs],
            ),
        ),
    )


def _build_boundary_continuation_anchors(
    *,
    outgoing_anchor_id: str,
    incoming_anchor_id: str,
    outgoing_token: str,
    incoming_token: str,
) -> tuple[SppmRouteAnchor, SppmRouteAnchor]:
    return (
        SppmRouteAnchor(
            anchor_id=outgoing_anchor_id,
            attrs=build_sppm_continuation_anchor_attrs(
                token=outgoing_token, is_secondary=False
            ),
        ),
        SppmRouteAnchor(
            anchor_id=incoming_anchor_id,
            attrs=build_sppm_continuation_anchor_attrs(
                token=incoming_token, is_secondary=False
            ),
        ),
    )


def _build_route_segment(
    *, source_id: str, target_id: str, attrs: list[str]
) -> SppmRouteSegment:
    return SppmRouteSegment(
        source_id=source_id, target_id=target_id, attrs=tuple(attrs)
    )


__all__ = [
    "SppmCorridorNode",
    "SppmEdgeRoute",
    "SppmRouteAnchor",
    "SppmRouteSegment",
    "SppmRoutingPlan",
    "_build_boundary_corridor_with_continuations",
    "_build_boundary_corridor_with_point_anchor",
    "_build_lr_boundary_corridor_direct",
    "_build_lr_boundary_corridor_with_continuations",
    "_build_non_boundary_continuation_route",
    "_build_non_rework_direct_route",
    "build_core_route_plan",
    "build_corridor_metadata",
    "collect_rework_branch_metadata",
    "collect_rework_return_sources",
    "edge_pairs",
    "edge_with_rework_metadata_policy",
    "node_kinds",
    "placement_for_routing",
    "resolve_lane_id",
]


def _build_non_boundary_continuation_route(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    resolved_ports: tuple[str, str] | None,
    outgoing_token: str,
    incoming_token: str,
    boundary_anchor_base: str,
) -> SppmEdgeRoute:
    """Build a non-boundary route that uses continuation anchors."""
    source_attrs = [resolved_ports[0]] if resolved_ports is not None else []
    target_attrs = [resolved_ports[1]] if resolved_ports is not None else []
    outgoing_anchor_id = f"{boundary_anchor_base}_out"
    incoming_anchor_id = f"{boundary_anchor_base}_in"
    anchors = _build_boundary_continuation_anchors(
        outgoing_anchor_id=outgoing_anchor_id,
        incoming_anchor_id=incoming_anchor_id,
        outgoing_token=outgoing_token,
        incoming_token=incoming_token,
    )
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="corridor",
        is_boundary=False,
        is_rework=False,
        lane_id=None,
        corridor_nodes=(),
        anchors=anchors,
        segments=(
            _build_route_segment(
                source_id=source,
                target_id=outgoing_anchor_id,
                attrs=[*source_attrs, "arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=outgoing_anchor_id,
                target_id=incoming_anchor_id,
                attrs=["arrowhead=none", "constraint=false", "weight=0"],
            ),
            _build_route_segment(
                source_id=incoming_anchor_id,
                target_id=target,
                attrs=[*target_attrs, *edge_attrs],
            ),
        ),
    )


def _build_non_rework_direct_route(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    is_boundary: bool,
    resolved_ports: tuple[str, str] | None,
) -> SppmEdgeRoute:
    """Build the direct non-rework route when no continuation anchors are needed."""
    segment_attrs = tuple(
        (list(resolved_ports) if resolved_ports is not None else []) + edge_attrs
    )
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="direct",
        is_boundary=is_boundary,
        is_rework=False,
        lane_id=None,
        corridor_nodes=(),
        anchors=(),
        segments=(
            SppmRouteSegment(source_id=source, target_id=target, attrs=segment_attrs),
        ),
    )
