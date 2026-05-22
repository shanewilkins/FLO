"""Renderer-agnostic placement core for FLO diagram layout."""

from .corridors import CorridorAnchor, CorridorLane, CorridorPlan, build_corridor_plan
from .elk_adapter import ElkEngine, layout_sppm_with_elk, layout_swimlane_with_elk
from .elk_errors import (
    ElkEngineError,
    ElkEngineProtocolError,
    ElkEngineSubprocessError,
    ElkEngineTimeoutError,
    ElkRuntimeUnavailableError,
)
from .elk import (
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
    build_flowchart_elk_layout_request,
    build_sppm_elk_layout_request,
    build_swimlane_elk_layout_request,
    execute_elk_layout,
    normalize_elk_layout_result,
    serialize_elk_layout_request,
)
from .elk_runtime import run_elkjs_layout
from .models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    LinePlacement,
    NodeMeasure,
    PlacementConstraints,
    PlacementPlan,
    RoutedEdgePath,
    serialize_layout_result,
)
from .placement import build_placement_plan
from .ports import PortSpec, build_port_assignments
from .routing import (
    EdgeRoute,
    RouteConflict,
    RoutePlan,
    build_route_plan,
    serialize_route_plan,
)

__all__ = [
    "CorridorLane",
    "CorridorAnchor",
    "CorridorPlan",
    "ElkEngine",
    "ElkEngineError",
    "ElkRuntimeUnavailableError",
    "ElkEngineSubprocessError",
    "ElkEngineTimeoutError",
    "ElkEngineProtocolError",
    "ElkLayoutLane",
    "ElkLayoutNode",
    "ElkLayoutEdge",
    "ElkLayoutRequest",
    "build_flowchart_elk_layout_request",
    "build_sppm_elk_layout_request",
    "execute_elk_layout",
    "PortSpec",
    "EdgeRoute",
    "LayoutPoint",
    "LayoutBounds",
    "LayoutLaneFrame",
    "RoutedEdgePath",
    "LayoutResult",
    "RouteConflict",
    "RoutePlan",
    "NodeMeasure",
    "PlacementConstraints",
    "LinePlacement",
    "PlacementPlan",
    "build_corridor_plan",
    "build_swimlane_elk_layout_request",
    "layout_sppm_with_elk",
    "layout_swimlane_with_elk",
    "normalize_elk_layout_result",
    "run_elkjs_layout",
    "serialize_elk_layout_request",
    "build_port_assignments",
    "build_placement_plan",
    "build_route_plan",
    "serialize_layout_result",
    "serialize_route_plan",
]
