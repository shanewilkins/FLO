"""Deterministic SPPM edge routing plan.

This module keeps routing decisions in FLO-owned data so layout regressions can
be detected before Graphviz turns the plan into geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._autoformat_wrap import WrapPlan, wrap_chunk_exit_anchor_id
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

    def route_for(self, source: str, target: str) -> SppmEdgeRoute | None:
        """Return the resolved route for a source-target edge pair, if any."""
        return self.routes.get((source, target))


@dataclass(frozen=True)
class SppmPortPolicy:
    """Node-level ingress/egress policy for SPPM routing."""

    secondary_line_targets: frozenset[str]


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

    return SppmRoutingPlan(routes=routes, corridor_plan=corridor_plan, route_plan=route_plan)


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


def _sppm_rework_ports(
    *,
    wrap_ports: tuple[str, str],
    is_branch_out: bool,
    source: str,
    target: str,
    source_kind: str,
    target_kind: str,
    core_route: Any | None,
    port_policy: SppmPortPolicy,
) -> tuple[str, str]:
    """Return rework ports that reduce crossings around the mainline.

        For LR layouts:
                - decision branch-out edges leave the diamond south tip and enter
                    rework at the top edge (south -> north)
                - return edges leave rework from the west side and re-enter mainline
                    from the west side

    For TB layouts:
    - branch-out edges leave rightward and enter from left (e -> w)
    - return edges leave leftward and re-enter from right (w -> e)
    """
    source_port, target_port = wrap_ports
    if source_port == "tailport=e" and target_port == "headport=w":
        # LR layout visual contract:
        # - decision branch-to-rework exits south and enters rework north
        # - other branch-to-rework edges enter rework from west
        # - rework-return leaves rework west and re-enters mainline west
        if is_branch_out:
            if source_kind == "decision":
                return ("tailport=s", "headport=n")
            return ("tailport=e", "headport=w")

        source_return_port = "tailport=w"
        if core_route is not None and _supports_named_ports(source_kind):
            source_return_port = _graphviz_tailport_for_side(
                slot_index=core_route.source_port.slot_index,
                side="w",
                kind=source_kind,
            )

        if core_route is not None and _supports_named_ports(target_kind):
            return (
                source_return_port,
                _graphviz_headport_for_side(
                    slot_index=core_route.target_port.slot_index,
                    side="w",
                    kind=target_kind,
                ),
            )
        return (source_return_port, "headport=w")
    if source_port == "tailport=s" and target_port == "headport=n":
        if is_branch_out:
            return ("tailport=e", "headport=w")
        return ("tailport=w", "headport=e")
    return (source_port, target_port)


def _build_sppm_port_policy(*, edges: list[dict[str, Any]], node_kinds: dict[str, str]) -> SppmPortPolicy:
    secondary_line_targets: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if not _edge_is_explicit_branch_out(edge=edge, source_kind=node_kinds.get(source, "task")):
            continue
        secondary_line_targets.add(target)
    return SppmPortPolicy(secondary_line_targets=frozenset(secondary_line_targets))


def _edge_is_explicit_branch_out(*, edge: dict[str, Any], source_kind: str) -> bool:
    if str(edge.get("edge_type") or "").strip().lower() != "rework" and edge.get("rework") is not True:
        return False
    return source_kind == "decision" or edge.get("outcome") is not None or edge.get("label") is not None


def _preferred_tailport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    slot_role: str,
    fallback_side: str,
    port_policy: SppmPortPolicy,
) -> str:
    _ = slot_role
    if node_id in port_policy.secondary_line_targets and core_route is not None:
        return _graphviz_tailport_for_side(
            slot_index=core_route.source_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    return f"tailport={fallback_side}"


def _preferred_headport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    slot_role: str,
    fallback_side: str,
    port_policy: SppmPortPolicy,
) -> str:
    _ = slot_role
    if node_id in port_policy.secondary_line_targets and core_route is not None:
        return _graphviz_headport_for_side(
            slot_index=core_route.target_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    if core_route is not None and _supports_named_ports(kind) and fallback_side in {"w", "e"}:
        return _graphviz_headport_for_side(
            slot_index=core_route.target_port.slot_index,
            side=fallback_side,
            kind=kind,
        )
    return f"headport={fallback_side}"


def _preferred_return_headport(
    *,
    node_id: str,
    kind: str,
    core_route: Any | None,
    fallback_side: str,
) -> str:
    _ = node_id
    if core_route is not None and _supports_named_ports(kind):
        return f'headport="rin_{core_route.target_port.slot_index}:e"'
    return f"headport={fallback_side}"


def _graphviz_tailport_for_side(*, slot_index: int, side: str, kind: str) -> str:
    if _supports_named_ports(kind):
        if side == "w":
            return f'tailport="in_{slot_index}:w"'
        return f'tailport="out_{slot_index}:{side}"'
    return f"tailport={side}"


def _graphviz_headport_for_side(*, slot_index: int, side: str, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'headport="in_{slot_index}:{side}"'
    return f"headport={side}"


def _build_boundary_lane_map(*, wrap_plan: WrapPlan) -> dict[tuple[str, str], str]:
    if not wrap_plan.active:
        return {}
    lane_map: dict[tuple[str, str], str] = {}
    for idx in range(max(0, len(wrap_plan.chunks) - 1)):
        source = wrap_plan.chunks[idx][-1]
        target = wrap_plan.chunks[idx + 1][0]
        lane_map[(source, target)] = f"wrap_lane_{idx}"
    return lane_map


def _resolved_ports(
    *,
    core_route: Any | None,
    options: RenderOptions,
    wrap_ports: tuple[str, str] | None,
    source_kind: str,
    target_kind: str,
) -> tuple[str, str]:
    if core_route is not None:
        return (
            f"tailport={core_route.source_port.side}",
            f"headport={core_route.target_port.side}",
        )
    if wrap_ports is not None:
        return wrap_ports
    return _sppm_wrap_ports(options=options)


def _graphviz_tailport_for_spec(port_spec: Any, *, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'tailport="out_{port_spec.slot_index}:{port_spec.side}"'
    return f"tailport={port_spec.side}"


def _graphviz_headport_for_spec(port_spec: Any, *, kind: str) -> str:
    if _supports_named_ports(kind):
        return f'headport="in_{port_spec.slot_index}:{port_spec.side}"'
    return f"headport={port_spec.side}"


def _supports_named_ports(kind: str) -> bool:
    return kind not in {"start", "end", "decision"}


def _resolved_boundary_ports(
    *,
    core_route: Any | None,
    options: RenderOptions,
    source_kind: str,
    target_kind: str,
) -> tuple[str, str]:
    if options.orientation == "lr":
        source_port = (
            _graphviz_tailport_for_spec(core_route.source_port, kind=source_kind)
            if core_route is not None
            else "tailport=e"
        )
        if _supports_named_ports(target_kind):
            return (source_port, 'headport="boundary_in:s"')
        return (source_port, "headport=n")

    if core_route is not None:
        return (
            f"tailport={core_route.source_port.side}",
            f"headport={core_route.target_port.side}",
        )
    return _sppm_wrap_ports(options=options)


def _sppm_wrap_ports(*, options: RenderOptions) -> tuple[str, str]:
    if options.orientation == "tb":
        return ("tailport=s", "headport=n")
    return ("tailport=e", "headport=w")


def sppm_rework_anchor_id(*, source: str, target: str) -> str:
    """Return a stable anchor id for a rework edge between two nodes."""
    source_part = _safe_sppm_edge_id_part(source)
    target_part = _safe_sppm_edge_id_part(target)
    return f"__sppm_rework_corridor_{source_part}_{target_part}"


def sppm_boundary_anchor_id(*, source: str, target: str) -> str:
    """Return a stable anchor id for a wrapped boundary edge bend point."""
    source_part = _safe_sppm_edge_id_part(source)
    target_part = _safe_sppm_edge_id_part(target)
    return f"__sppm_boundary_corridor_{source_part}_{target_part}"


def _safe_sppm_edge_id_part(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned) or "edge"


def is_sppm_rework_edge(
    *,
    edge: dict[str, Any],
    step_numbering: dict[str, int],
    source: str,
    target: str,
) -> bool:
    """Return whether an SPPM edge should be rendered as rework."""
    explicit = edge.get("rework")
    if explicit is not None:
        return bool(explicit)
    if str(edge.get("edge_type") or "").strip().lower() == "rework":
        return True

    src_num = step_numbering.get(source)
    dst_num = step_numbering.get(target)
    if src_num is None or dst_num is None:
        return False
    return src_num > dst_num