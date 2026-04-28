"""Renderer-agnostic placement core for FLO diagram layout."""

from .corridors import CorridorAnchor, CorridorLane, CorridorPlan, build_corridor_plan
from .models import (
    LinePlacement,
    NodeMeasure,
    PlacementConstraints,
    PlacementPlan,
)
from .placement import build_placement_plan
from .ports import PortSpec, build_port_assignments
from .routing import EdgeRoute, RouteConflict, RoutePlan, build_route_plan, serialize_route_plan

__all__ = [
    "CorridorLane",
    "CorridorAnchor",
    "CorridorPlan",
    "PortSpec",
    "EdgeRoute",
    "RouteConflict",
    "RoutePlan",
    "NodeMeasure",
    "PlacementConstraints",
    "LinePlacement",
    "PlacementPlan",
    "build_corridor_plan",
    "build_port_assignments",
    "build_placement_plan",
    "build_route_plan",
    "serialize_route_plan",
]
