"""Deterministic route planning on placement and corridor core plans."""

from __future__ import annotations

from dataclasses import dataclass

from .corridors import CorridorPlan
from .models import PlacementPlan
from .ports import PortSpec, build_port_assignments


@dataclass(frozen=True)
class RouteConflict:
    """Stable summary of a shared-lane conflict outcome."""

    lane_id: str
    edges: tuple[tuple[str, str], ...]
    policy: str


@dataclass(frozen=True)
class EdgeRoute:
    """Resolved route metadata for one logical edge."""

    edge: tuple[str, str]
    source_port: PortSpec
    lane_hops: tuple[str, ...]
    target_port: PortSpec
    is_boundary: bool


@dataclass(frozen=True)
class RoutePlan:
    """All resolved routes and conflict outcomes for one diagram."""

    routes: dict[tuple[str, str], EdgeRoute]
    conflicts: tuple[RouteConflict, ...]

    def route_for(self, source: str, target: str) -> EdgeRoute | None:
        """Return the resolved route for a source-target edge pair, if any."""
        return self.routes.get((source, target))


def build_route_plan(
    *,
    placement: PlacementPlan,
    corridor: CorridorPlan,
    edges: list[tuple[str, str]],
) -> RoutePlan:
    """Build a deterministic route plan from shared core plans."""
    source_ports, target_ports = build_port_assignments(placement=placement, edges=edges)
    routes: dict[tuple[str, str], EdgeRoute] = {}
    for edge in sorted(edges):
        source_port = source_ports.get(edge)
        target_port = target_ports.get(edge)
        if source_port is None or target_port is None:
            continue
        lane_hops = corridor.edge_lane_hops.get(edge, ())
        routes[edge] = EdgeRoute(
            edge=edge,
            source_port=source_port,
            lane_hops=lane_hops,
            target_port=target_port,
            is_boundary=bool(lane_hops),
        )
    return RoutePlan(routes=routes, conflicts=_conflicts_from_corridor(corridor))


def serialize_route_plan(plan: RoutePlan) -> str:
    """Return a stable snapshot of core route-plan decisions."""
    lines: list[str] = []
    for edge in sorted(plan.routes.keys()):
        route = plan.routes[edge]
        source, target = edge
        lines.append(f"edge {source}->{target} boundary={route.is_boundary}")
        lines.append(
            f"  source {route.source_port.node_id}:{route.source_port.side}[{route.source_port.slot_index}]"
        )
        if route.lane_hops:
            lines.append(f"  lanes {', '.join(route.lane_hops)}")
        else:
            lines.append("  lanes -")
        lines.append(
            f"  target {route.target_port.node_id}:{route.target_port.side}[{route.target_port.slot_index}]"
        )
    for conflict in plan.conflicts:
        edge_list = ", ".join(f"{source}->{target}" for source, target in conflict.edges)
        lines.append(f"conflict {conflict.lane_id} policy={conflict.policy} edges={edge_list}")
    return "\n".join(lines)


def _conflicts_from_corridor(corridor: CorridorPlan) -> tuple[RouteConflict, ...]:
    conflicts: list[RouteConflict] = []
    for lane_id, edges in sorted(corridor.lane_occupancy.items()):
        if len(edges) <= 1:
            continue
        conflicts.append(RouteConflict(lane_id=lane_id, edges=edges, policy="share-lane-stacked"))
    return tuple(conflicts)