"""Deterministic SPPM edge routing plan.

This module keeps routing decisions in FLO-owned data so layout regressions can
be detected before Graphviz turns the plan into geometry.
"""

from __future__ import annotations

from typing import Any

from ._autoformat_wrap import WrapPlan, wrap_chunk_exit_anchor_id
from ._sppm_continuation_labels import (
    build_sppm_continuation_anchor_attrs,
    resolve_sppm_continuation_anchor_tokens,
)
from ._sppm_rework_databox import build_sppm_rework_data_box_attrs
from ._sppm_postprocess_contract import build_svg_postprocess_contract
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
from ._sppm_routing_support import (
    SppmEdgeRoute,
    SppmRouteAnchor,
    SppmRouteSegment,
    SppmRoutingPlan,
    _build_boundary_corridor_with_continuations,
    _build_boundary_corridor_with_point_anchor,
    build_core_route_plan,
    build_corridor_metadata,
    _build_lr_boundary_corridor_direct,
    _build_lr_boundary_corridor_with_continuations,
    _build_non_boundary_continuation_route,
    _build_non_rework_direct_route,
    collect_rework_branch_metadata,
    collect_rework_return_sources,
    edge_pairs,
    edge_with_rework_metadata_policy,
    node_kinds,
    placement_for_routing,
    resolve_lane_id,
)
from .options import RenderOptions


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
    edge_pairs_list = edge_pairs(edges)
    placement = placement_for_routing(nodes=nodes, options=options, wrap_plan=wrap_plan)
    corridor_plan = build_corridor_metadata(placement=placement, edge_pairs=edge_pairs_list)
    route_plan = build_core_route_plan(
        placement=placement,
        edge_pairs=edge_pairs_list,
        corridor_plan=corridor_plan,
    )
    node_kinds_by_id = node_kinds(nodes)
    port_policy = _build_sppm_port_policy(edges=edges, node_kinds=node_kinds_by_id)
    branch_metadata_by_rework_target = collect_rework_branch_metadata(edges=edges, node_kinds=node_kinds_by_id)
    rework_return_sources = collect_rework_return_sources(
        edges=edges,
        step_numbering=step_numbering,
        node_kinds=node_kinds_by_id,
        branch_metadata_by_rework_target=branch_metadata_by_rework_target,
    )

    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue

        effective_edge = edge_with_rework_metadata_policy(
            edge=edge,
            source=source,
            target=target,
            step_numbering=step_numbering,
            node_kinds=node_kinds_by_id,
            branch_metadata_by_rework_target=branch_metadata_by_rework_target,
            rework_return_sources=rework_return_sources,
        )

        route = _build_sppm_edge_route(
            edge=effective_edge,
            source=source,
            target=target,
            options=options,
            step_numbering=step_numbering,
            wrap_plan=wrap_plan,
            wrap_ports=wrap_ports,
            lane_id=resolve_lane_id(
                edge=(source, target),
                route_plan=route_plan,
                boundary_lanes=boundary_lanes,
            ),
            core_route=route_plan.route_for(source, target),
            source_kind=node_kinds_by_id.get(source, "task"),
            target_kind=node_kinds_by_id.get(target, "task"),
            port_policy=port_policy,
        )
        routes[(source, target)] = route

    # Build postprocess contract for SVG rewrites
    contract = build_svg_postprocess_contract(
        routes=routes,
        wrap_active=wrap_plan.active,
        node_kinds=node_kinds_by_id,
    )
    return SppmRoutingPlan(
        routes=routes,
        corridor_plan=corridor_plan,
        route_plan=route_plan,
        svg_postprocess_contract=contract,
    )


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
    edge_attrs = _base_sppm_edge_attrs(
        source=source,
        target=target,
        options=options,
        step_numbering=step_numbering,
    )

    is_rework = is_sppm_rework_edge(
        edge=edge,
        step_numbering=step_numbering,
        source=source,
        target=target,
    )
    is_boundary = wrap_plan.active and (source, target) in wrap_plan.boundary_edges
    if is_boundary and not is_rework:
        edge_attrs.extend(["minlen=2", "penwidth=1.2"])
    _append_non_rework_branch_label(edge_attrs=edge_attrs, edge=edge, is_rework=is_rework)
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
            wrap_plan=wrap_plan,
            is_boundary=is_boundary,
            wrap_ports=resolved_ports,
            is_branch_out=is_branch_out,
            source_kind=source_kind,
            target_kind=target_kind,
            core_route=core_route,
            port_policy=port_policy,
        )

    return _build_non_rework_route(
        edge=edge,
        source=source,
        target=target,
        edge_attrs=edge_attrs,
        is_boundary=is_boundary,
        resolved_ports=resolved_ports,
        core_route=core_route,
        options=options,
        source_kind=source_kind,
        target_kind=target_kind,
        lane_id=lane_id,
        wrap_plan=wrap_plan,
    )


def _base_sppm_edge_attrs(
    *,
    source: str,
    target: str,
    options: RenderOptions,
    step_numbering: dict[str, int],
) -> list[str]:
    edge_attrs: list[str] = []
    if options.sppm_step_numbering != "edge":
        return edge_attrs
    src_num = step_numbering.get(source)
    dst_num = step_numbering.get(target)
    if src_num is not None and dst_num is not None:
        edge_attrs.append(f'xlabel="{src_num}->{dst_num}"')
    return edge_attrs


def _append_non_rework_branch_label(*, edge_attrs: list[str], edge: dict[str, Any], is_rework: bool) -> None:
    if is_rework or any(attr.startswith("xlabel=") for attr in edge_attrs):
        return
    branch_label = edge.get("outcome") or edge.get("label")
    if branch_label is not None:
        edge_attrs.append(f'xlabel="{str(branch_label)}"')
        edge_attrs.append('fontcolor="#455A64"')


def _build_non_rework_route(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    edge_attrs: list[str],
    is_boundary: bool,
    resolved_ports: tuple[str, str] | None,
    core_route: Any | None,
    options: RenderOptions,
    source_kind: str,
    target_kind: str,
    lane_id: str | None,
    wrap_plan: WrapPlan,
) -> SppmEdgeRoute:
    outgoing_token, incoming_token = resolve_sppm_continuation_anchor_tokens(
        edge=edge,
        source=source,
        target=target,
        wrap_plan=wrap_plan,
    )

    if is_boundary and resolved_ports is not None:
        boundary_ports = _resolved_boundary_ports(
            core_route=core_route,
            options=options,
            source_kind=source_kind,
            target_kind=target_kind,
        )
        return _build_boundary_corridor_route(
            edge=edge,
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            wrap_ports=boundary_ports,
            lane_id=lane_id or "wrap_lane_unknown",
            wrap_plan=wrap_plan,
            options=options,
        )

    if outgoing_token is not None and incoming_token is not None:
        boundary_anchor_base = sppm_boundary_anchor_id(source=source, target=target)
        return _build_non_boundary_continuation_route(
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            resolved_ports=resolved_ports,
            outgoing_token=outgoing_token,
            incoming_token=incoming_token,
            boundary_anchor_base=boundary_anchor_base,
        )

    return _build_non_rework_direct_route(
        source=source,
        target=target,
        is_boundary=is_boundary,
        edge_attrs=edge_attrs,
        resolved_ports=resolved_ports,
    )


def _build_boundary_corridor_route(
    *,
    edge: dict[str, Any],
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
    outgoing_token, incoming_token = resolve_sppm_continuation_anchor_tokens(
        edge=edge,
        source=source,
        target=target,
        wrap_plan=wrap_plan,
    )
    boundary_anchor_base = sppm_boundary_anchor_id(source=source, target=target)

    if options.orientation == "lr" and chunk_idx is not None:
        exit_anchor_id = wrap_chunk_exit_anchor_id(orientation="lr", chunk_idx=chunk_idx)
        if outgoing_token is not None and incoming_token is not None:
            return _build_lr_boundary_corridor_with_continuations(
                source=source,
                target=target,
                edge_attrs=edge_attrs,
                source_port=source_port,
                target_port=target_port,
                lane_id=lane_id,
                exit_anchor_id=exit_anchor_id,
                boundary_anchor_base=boundary_anchor_base,
                outgoing_token=outgoing_token,
                incoming_token=incoming_token,
            )
        return _build_lr_boundary_corridor_direct(
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            source_port=source_port,
            target_port=target_port,
            lane_id=lane_id,
            exit_anchor_id=exit_anchor_id,
        )

    _ = lane_id
    if outgoing_token is not None and incoming_token is not None:
        return _build_boundary_corridor_with_continuations(
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            source_port=source_port,
            target_port=target_port,
            lane_id=lane_id,
            boundary_anchor_base=boundary_anchor_base,
            outgoing_token=outgoing_token,
            incoming_token=incoming_token,
        )

    return _build_boundary_corridor_with_point_anchor(
        source=source,
        target=target,
        edge_attrs=edge_attrs,
        source_port=source_port,
        target_port=target_port,
        lane_id=lane_id,
        anchor_id=boundary_anchor_base,
    )


def _build_rework_route(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    edge_attrs: list[str],
    wrap_plan: WrapPlan,
    is_boundary: bool,
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
    outgoing_token, incoming_token = resolve_sppm_continuation_anchor_tokens(
        edge=edge,
        source=source,
        target=target,
        wrap_plan=wrap_plan,
    )
    anchor_id = sppm_rework_anchor_id(source=source, target=target)
    suppress_databox = bool(edge.get("_sppm_suppress_rework_databox"))
    rework_data_box_attrs = (
        None
        if suppress_databox
        else build_sppm_rework_data_box_attrs(edge.get("metadata"), is_branch_out=is_branch_out)
    )
    anchor = SppmRouteAnchor(
        anchor_id=anchor_id,
        attrs=_build_rework_anchor_attrs(
            is_boundary=is_boundary,
            incoming_token=incoming_token,
            outgoing_token=outgoing_token,
        ),
    )
    first_segment_attrs = _build_rework_first_segment_attrs(
        source_port=source_port,
        route_attrs=route_attrs,
        rework_data_box_attrs=rework_data_box_attrs,
        is_branch_out=is_branch_out,
    )
    second_segment_attrs = _build_rework_second_segment_attrs(
        target_port=target_port,
        route_attrs=route_attrs,
        rework_data_box_attrs=rework_data_box_attrs,
        is_branch_out=is_branch_out,
        branch_label=edge.get("outcome") or edge.get("label"),
    )

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


def _build_rework_anchor_attrs(
    *,
    is_boundary: bool,
    incoming_token: str | None,
    outgoing_token: str | None,
) -> tuple[str, ...]:
    if is_boundary and incoming_token is not None:
        return build_sppm_continuation_anchor_attrs(token=incoming_token, is_secondary=True)
    if is_boundary and outgoing_token is not None:
        return build_sppm_continuation_anchor_attrs(token=outgoing_token, is_secondary=True)
    return ("shape=point", "width=0.01", "height=0.01", 'label=""', "style=invis")


def _build_rework_first_segment_attrs(
    *,
    source_port: str,
    route_attrs: list[str],
    rework_data_box_attrs: tuple[str, ...] | None,
    is_branch_out: bool,
) -> tuple[str, ...]:
    filtered_attrs = tuple(
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
    if rework_data_box_attrs is not None and is_branch_out:
        return tuple([*filtered_attrs, *rework_data_box_attrs])
    return filtered_attrs


def _build_rework_second_segment_attrs(
    *,
    target_port: str,
    route_attrs: list[str],
    rework_data_box_attrs: tuple[str, ...] | None,
    is_branch_out: bool,
    branch_label: object | None,
) -> tuple[str, ...]:
    attrs = [target_port, *route_attrs]
    if rework_data_box_attrs is not None and not is_branch_out:
        attrs.extend(rework_data_box_attrs)
    if branch_label is not None:
        attrs.append(f'xlabel="{str(branch_label)}"')
    return tuple(attrs)


