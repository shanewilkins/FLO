"""Deterministic SPPM edge routing plan.

This module keeps routing decisions in FLO-owned data so layout regressions can
be detected before Graphviz turns the plan into geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._autoformat_wrap import WrapPlan, wrap_chunk_exit_anchor_id
from ._sppm_postprocess_contract import SppmSvgPostprocessContract, build_svg_postprocess_contract
from ._sppm_port_policy import (
    SppmPortPolicy,
    _build_sppm_port_policy,
    _sppm_rework_ports,
    _resolved_ports,
    _resolved_boundary_ports,
    _build_boundary_lane_map,
    _sppm_wrap_ports,
    sppm_rework_anchor_id,
    sppm_boundary_anchor_id,
    is_sppm_rework_edge,
)
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


def serialize_sppm_routing_plan(plan: SppmRoutingPlan) -> str:
    """Return a stable, human-readable snapshot of route decisions."""
    lines: list[str] = []
    for source, target in sorted(plan.routes.keys()):
        route = plan.routes[(source, target)]
        lines.append(
            f"edge {source}->{target} kind={route.kind} boundary={route.is_boundary} rework={route.is_rework}"
        )
        if route.lane_id is not None:
            lines.append(f"  lane {route.lane_id}")
        for corridor_node in route.corridor_nodes:
            lines.append(
                f"  corridor {corridor_node.role} {corridor_node.node_id} [{', '.join(corridor_node.attrs)}]"
            )
        for anchor in route.anchors:
            lines.append(f"  anchor {anchor.anchor_id} [{', '.join(anchor.attrs)}]")
        for segment in route.segments:
            lines.append(
                f"  segment {segment.source_id}->{segment.target_id} [{', '.join(segment.attrs)}]"
            )
    return "\n".join(lines)


def build_sppm_routing_plan(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
) -> SppmRoutingPlan:
    """Build deterministic route metadata for SPPM edges."""
    routes: dict[tuple[str, str], SppmEdgeRoute] = {}
    wrap_ports = _sppm_wrap_ports(options=options) if wrap_plan.active else None
    boundary_lanes = _build_boundary_lane_map(wrap_plan=wrap_plan)
    edge_pairs = _edge_pairs(edges)
    placement = _placement_for_routing(nodes=nodes, options=options, wrap_plan=wrap_plan)
    corridor_plan = _build_corridor_metadata(placement=placement, edge_pairs=edge_pairs)
    route_plan = _build_core_route_plan(
        placement=placement,
        edge_pairs=edge_pairs,
        corridor_plan=corridor_plan,
    )
    node_kinds = _node_kinds(nodes)
    port_policy = _build_sppm_port_policy(edges=edges, node_kinds=node_kinds)

    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue

        route = _build_sppm_edge_route(
            edge=edge,
            source=source,
            target=target,
            options=options,
            step_numbering=step_numbering,
            wrap_plan=wrap_plan,
            wrap_ports=wrap_ports,
            lane_id=_resolve_lane_id(
                edge=(source, target),
                route_plan=route_plan,
                boundary_lanes=boundary_lanes,
            ),
            core_route=route_plan.route_for(source, target),
            source_kind=node_kinds.get(source, "task"),
            target_kind=node_kinds.get(target, "task"),
            port_policy=port_policy,
        )
        routes[(source, target)] = route

    # Build postprocess contract for SVG rewrites
    contract = build_svg_postprocess_contract(routes=routes, wrap_active=wrap_plan.active)
    return SppmRoutingPlan(
        routes=routes,
        corridor_plan=corridor_plan,
        route_plan=route_plan,
        svg_postprocess_contract=contract,
    )


def _edge_pairs(edges: list[dict[str, Any]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source and target:
            pairs.append((source, target))
    return pairs


def _build_corridor_metadata(*, placement: PlacementPlan, edge_pairs: list[tuple[str, str]]) -> CorridorPlan:
    if len(placement.lines) <= 1:
        return CorridorPlan(
            lanes=(),
            entry_anchors={},
            exit_anchors={},
            lane_occupancy={},
            edge_lane_hops={},
        )
    return build_corridor_plan(placement=placement, edges=edge_pairs)


def _build_core_route_plan(
    *,
    placement: PlacementPlan,
    edge_pairs: list[tuple[str, str]],
    corridor_plan: CorridorPlan,
) -> RoutePlan:
    return build_route_plan(placement=placement, corridor=corridor_plan, edges=edge_pairs)


def _placement_for_routing(
    *,
    nodes: list[dict[str, Any]],
    options: RenderOptions,
    wrap_plan: WrapPlan,
) -> PlacementPlan:
    if wrap_plan.placement_plan is not None:
        return wrap_plan.placement_plan

    line_node_ids = wrap_plan.chunks if wrap_plan.active and wrap_plan.chunks else [_ordered_node_ids(nodes)]
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


def _ordered_node_ids(nodes: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id:
            ordered.append(node_id)
    return ordered


def _node_kinds(nodes: list[dict[str, Any]]) -> dict[str, str]:
    kinds: dict[str, str] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        kinds[node_id] = str(node.get("kind") or node.get("type") or "task").strip().lower()
    return kinds


def _resolve_lane_id(
    *,
    edge: tuple[str, str],
    route_plan: RoutePlan,
    boundary_lanes: dict[tuple[str, str], str],
) -> str | None:
    if edge in boundary_lanes:
        return boundary_lanes[edge]
    core_route = route_plan.route_for(edge[0], edge[1])
    if core_route is not None and core_route.lane_hops:
        return core_route.lane_hops[0]
    return None


def _build_sppm_edge_route(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    wrap_ports: tuple[str, str] | None,
    lane_id: str | None,
    core_route: Any | None,
    source_kind: str,
    target_kind: str,
    port_policy: SppmPortPolicy,
) -> SppmEdgeRoute:
    edge_attrs: list[str] = []
    if options.sppm_step_numbering == "edge":
        src_num = step_numbering.get(source)
        dst_num = step_numbering.get(target)
        if src_num is not None and dst_num is not None:
            edge_attrs.append(f'xlabel="{src_num}->{dst_num}"')

    is_rework = is_sppm_rework_edge(
        edge=edge,
        step_numbering=step_numbering,
        source=source,
        target=target,
    )
    is_boundary = wrap_plan.active and (source, target) in wrap_plan.boundary_edges
    if is_boundary and not is_rework:
        edge_attrs.extend(["minlen=2", "penwidth=1.2"])
    resolved_ports = _resolved_ports(
        core_route=core_route,
        options=options,
        wrap_ports=wrap_ports,
        source_kind=source_kind,
        target_kind=target_kind,
    )

    if is_rework:
        is_branch_out = source_kind == "decision" or edge.get("outcome") is not None or edge.get("label") is not None
        return _build_rework_route(
            edge=edge,
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            wrap_ports=resolved_ports,
            is_branch_out=is_branch_out,
            source_kind=source_kind,
            target_kind=target_kind,
            core_route=core_route,
            port_policy=port_policy,
        )

    if is_boundary and resolved_ports is not None:
        boundary_ports = _resolved_boundary_ports(
            core_route=core_route,
            options=options,
            source_kind=source_kind,
            target_kind=target_kind,
        )
        return _build_boundary_corridor_route(
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            wrap_ports=boundary_ports,
            lane_id=lane_id or "wrap_lane_unknown",
            wrap_plan=wrap_plan,
            options=options,
        )

    segment_attrs = tuple((list(resolved_ports) if resolved_ports is not None else []) + edge_attrs)
    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="direct",
        is_boundary=is_boundary,
        is_rework=False,
        lane_id=None,
        corridor_nodes=(),
        anchors=(),
        segments=(SppmRouteSegment(source_id=source, target_id=target, attrs=segment_attrs),),
    )


def _build_boundary_corridor_route(
    *,
    source: str,
    target: str,
    edge_attrs: list[str],
    wrap_ports: tuple[str, str],
    lane_id: str,
    wrap_plan: WrapPlan,
    options: RenderOptions,
) -> SppmEdgeRoute:
    source_port, target_port = wrap_ports
    chunk_idx = wrap_plan.node_chunk_index.get(source)

    if options.orientation == "lr" and chunk_idx is not None:
        exit_anchor_id = wrap_chunk_exit_anchor_id(orientation="lr", chunk_idx=chunk_idx)
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
                SppmRouteSegment(
                    source_id=source,
                    target_id=exit_anchor_id,
                    attrs=tuple([source_port, "arrowhead=none", "constraint=false", "weight=0"]),
                ),
                SppmRouteSegment(
                    source_id=exit_anchor_id,
                    target_id=target,
                    attrs=tuple([target_port, *edge_attrs]),
                ),
            ),
        )

    _ = lane_id
    anchor_id = sppm_boundary_anchor_id(source=source, target=target)
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
            SppmRouteSegment(
                source_id=source,
                target_id=anchor_id,
                attrs=tuple([source_port, "arrowhead=none", "constraint=false", "weight=0"]),
            ),
            SppmRouteSegment(
                source_id=anchor_id,
                target_id=target,
                attrs=tuple([target_port, *edge_attrs]),
            ),
        ),
    )


def _build_rework_route(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    edge_attrs: list[str],
    wrap_ports: tuple[str, str],
    is_branch_out: bool,
    source_kind: str,
    target_kind: str,
    core_route: Any | None,
    port_policy: SppmPortPolicy,
) -> SppmEdgeRoute:
    # Route rework loops off the primary spine with directional ports:
    # - branch-out (typically decision -> rework): move away from mainline
    # - return-loop (rework -> mainline): re-enter from the opposite side
    source_port, target_port = _sppm_rework_ports(
        wrap_ports=wrap_ports,
        is_branch_out=is_branch_out,
        source=source,
        target=target,
        source_kind=source_kind,
        target_kind=target_kind,
        core_route=core_route,
        port_policy=port_policy,
    )
    route_attrs = ["constraint=false", "minlen=3", "weight=0", "style=dashed", *edge_attrs]
    anchor_id = sppm_rework_anchor_id(source=source, target=target)
    anchor = SppmRouteAnchor(
        anchor_id=anchor_id,
        attrs=("shape=point", "width=0.01", "height=0.01", 'label=""', "style=invis"),
    )
    first_segment_attrs = tuple(
        [
            source_port,
            *[
                attr
                for attr in route_attrs
                if not attr.startswith("label=")
                and not attr.startswith("xlabel=")
                and not attr.startswith("minlen=")
                and not attr.startswith("penwidth=")
                and not attr.startswith("weight=")
            ],
            "weight=0",
            "arrowhead=none",
        ]
    )
    second_segment_attrs = list([target_port, *route_attrs])
    branch_label = edge.get("outcome") or edge.get("label")
    if branch_label is not None:
        second_segment_attrs.append(f'xlabel="{str(branch_label)}"')

    return SppmEdgeRoute(
        source=source,
        target=target,
        kind="rework",
        is_boundary=False,
        is_rework=True,
        lane_id=None,
        corridor_nodes=(),
        anchors=(anchor,),
        segments=(
            SppmRouteSegment(source_id=source, target_id=anchor_id, attrs=first_segment_attrs),
            SppmRouteSegment(source_id=anchor_id, target_id=target, attrs=tuple(second_segment_attrs)),
        ),
    )
