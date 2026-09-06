"""Renderer-agnostic placement core for FLO diagram layout."""

from flo.render._diagnostics import RenderDiagnostic

from .corridors import CorridorAnchor, CorridorLane, CorridorPlan, build_corridor_plan
from .elk import (
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
    execute_elk_layout,
    normalize_elk_layout_result,
    serialize_elk_layout_request,
)
from .elk_errors import (
    ElkEngineError,
    ElkEngineProtocolError,
    ElkEngineSubprocessError,
    ElkEngineTimeoutError,
    ElkRuntimeUnavailableError,
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
    "CorridorAnchor",
    "CorridorLane",
    "CorridorPlan",
    "EdgeRoute",
    "ElkEngineError",
    "ElkEngineProtocolError",
    "ElkEngineSubprocessError",
    "ElkEngineTimeoutError",
    "ElkLayoutEdge",
    "ElkLayoutLane",
    "ElkLayoutNode",
    "ElkLayoutRequest",
    "ElkRuntimeUnavailableError",
    "LayoutBounds",
    "LayoutLaneFrame",
    "LayoutPoint",
    "LayoutResult",
    "LinePlacement",
    "NodeMeasure",
    "PlacementConstraints",
    "PlacementPlan",
    "PortSpec",
    "RenderDiagnostic",
    "RouteConflict",
    "RoutePlan",
    "RoutedEdgePath",
    "build_corridor_plan",
    "build_placement_plan",
    "build_port_assignments",
    "build_route_plan",
    "execute_elk_layout",
    "normalize_elk_layout_result",
    "run_elkjs_layout",
    "serialize_elk_layout_request",
    "serialize_layout_result",
    "serialize_route_plan",
]
