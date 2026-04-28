"""Deterministic SPPM edge routing plan.

This module keeps routing decisions in FLO-owned data so layout regressions can
be detected before Graphviz turns the plan into geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._autoformat_wrap import AutoformatWrapPlan
from .options import RenderOptions


@dataclass(frozen=True)
class SppmRouteAnchor:
    anchor_id: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmCorridorNode:
    node_id: str
    lane_id: str
    role: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmRouteSegment:
    source_id: str
    target_id: str
    attrs: tuple[str, ...]


@dataclass(frozen=True)
class SppmEdgeRoute:
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
    routes: dict[tuple[str, str], SppmEdgeRoute]

    def route_for(self, source: str, target: str) -> SppmEdgeRoute | None:
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
    edges: list[dict[str, Any]],
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: AutoformatWrapPlan,
) -> SppmRoutingPlan:
    routes: dict[tuple[str, str], SppmEdgeRoute] = {}
    wrap_ports = _sppm_wrap_ports(options=options) if wrap_plan.active else None
    boundary_lanes = _build_boundary_lane_map(wrap_plan=wrap_plan)

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
            lane_id=boundary_lanes.get((source, target)),
        )
        routes[(source, target)] = route

    return SppmRoutingPlan(routes=routes)


def _build_sppm_edge_route(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: AutoformatWrapPlan,
    wrap_ports: tuple[str, str] | None,
    lane_id: str | None,
) -> SppmEdgeRoute:
    edge_attrs: list[str] = []
    if options.sppm_step_numbering == "edge":
        src_num = step_numbering.get(source)
        dst_num = step_numbering.get(target)
        if src_num is not None and dst_num is not None:
            edge_attrs.append(f'xlabel="{src_num}->{dst_num}"')

    is_boundary = wrap_plan.active and (source, target) in wrap_plan.boundary_edges
    if is_boundary:
        edge_attrs.extend(["minlen=2", "penwidth=1.2"])

    is_rework = is_sppm_rework_edge(
        edge=edge,
        step_numbering=step_numbering,
        source=source,
        target=target,
    )
    if is_rework:
        return _build_rework_route(
            edge=edge,
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            wrap_ports=wrap_ports or _sppm_wrap_ports(options=options),
        )

    if is_boundary and wrap_ports is not None:
        return _build_boundary_corridor_route(
            source=source,
            target=target,
            edge_attrs=edge_attrs,
            wrap_ports=wrap_ports,
            lane_id=lane_id or "wrap_lane_unknown",
        )

    segment_attrs = tuple((list(wrap_ports) if wrap_ports is not None else []) + edge_attrs)
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
) -> SppmEdgeRoute:
    source_port, target_port = wrap_ports
    _ = lane_id

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
                target_id=target,
                attrs=tuple([source_port, target_port, *edge_attrs]),
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
) -> SppmEdgeRoute:
    source_port, target_port = wrap_ports
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
        second_segment_attrs.append(f'label="{str(branch_label)}"')

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


def _build_boundary_lane_map(*, wrap_plan: AutoformatWrapPlan) -> dict[tuple[str, str], str]:
    if not wrap_plan.active:
        return {}
    lane_map: dict[tuple[str, str], str] = {}
    for idx in range(max(0, len(wrap_plan.chunks) - 1)):
        source = wrap_plan.chunks[idx][-1]
        target = wrap_plan.chunks[idx + 1][0]
        lane_map[(source, target)] = f"wrap_lane_{idx}"
    return lane_map


def _sppm_wrap_ports(*, options: RenderOptions) -> tuple[str, str]:
    if options.orientation == "tb":
        return ("tailport=s", "headport=n")
    return ("tailport=e", "headport=w")


def sppm_rework_anchor_id(*, source: str, target: str) -> str:
    source_part = _safe_sppm_edge_id_part(source)
    target_part = _safe_sppm_edge_id_part(target)
    return f"__sppm_rework_corridor_{source_part}_{target_part}"


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