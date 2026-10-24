"""ELK-friendly layout request API and result normalization."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from flo.errors import RenderError
from flo.render._diagnostics import RenderDiagnostic, RenderDiagnosticSeverity

from .elk_contracts import (
    ElkDirection,
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
)
from .elk_errors import ElkEngineProtocolError
from .models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from .serialization import serialize_elk_layout_request
from .trace import ElkLayoutTrace, LayoutObserver


def normalize_elk_layout_result(
    payload: dict[str, Any],
    *,
    request: ElkLayoutRequest,
) -> LayoutResult:
    """Normalize an ELK-style response payload into backend-neutral geometry."""
    root_bounds = LayoutBounds(
        x_px=_float_value(payload.get("x")),
        y_px=_float_value(payload.get("y")),
        width_px=_float_value(payload.get("width")),
        height_px=_float_value(payload.get("height")),
    )
    node_ids = {node.id for node in request.nodes}
    lane_order = [lane.id for lane in request.lanes]
    lane_labels = {lane.id: lane.label for lane in request.lanes}
    lane_members = {lane.id: lane.node_ids for lane in request.lanes}
    strict = request.strict_diagnostics

    node_bounds: dict[str, LayoutBounds] = {}
    lane_frames: dict[str, LayoutLaneFrame] = {}
    diagnostics: list[RenderDiagnostic] = []
    container_origins: dict[str, LayoutPoint] = {
        str(payload.get("id") or ""): LayoutPoint(
            x_px=root_bounds.x_px,
            y_px=root_bounds.y_px,
        )
    }
    _collect_child_geometry(
        graph=payload,
        parent_origin=LayoutPoint(x_px=root_bounds.x_px, y_px=root_bounds.y_px),
        node_ids=node_ids,
        lane_ids=set(lane_order),
        lane_labels=lane_labels,
        lane_members=lane_members,
        node_bounds=node_bounds,
        lane_frames=lane_frames,
        container_origins=container_origins,
        diagnostics=diagnostics,
        strict=strict,
    )

    edge_paths: dict[tuple[str, str], RoutedEdgePath] = {}
    edge_labels, edge_callouts, edge_rework, edge_tokens, edge_ports = (
        _edge_metadata_maps(request=request)
    )
    allowed_edges = {(edge.source_id, edge.target_id) for edge in request.edges}
    port_owner = _port_owner_map(request=request)
    _collect_edge_geometry(
        ignored_edge_ids={
            str(edge["id"]) for edge in request.serialization.auxiliary_edges
        },
        graph=payload,
        parent_origin=LayoutPoint(x_px=root_bounds.x_px, y_px=root_bounds.y_px),
        edge_labels=edge_labels,
        edge_callouts=edge_callouts,
        edge_rework=edge_rework,
        edge_tokens=edge_tokens,
        edge_ports=edge_ports,
        allowed_edges=allowed_edges,
        port_owner=port_owner,
        container_origins=container_origins,
        edge_paths=edge_paths,
        diagnostics=diagnostics,
        strict=strict,
    )
    _finalize_layout_diagnostics(
        request=request,
        lane_order=lane_order,
        lane_frames=lane_frames,
        edge_paths=edge_paths,
        allowed_edges=allowed_edges,
        diagnostics=diagnostics,
        strict=strict,
    )
    result = LayoutResult(
        orientation="tb" if request.direction == "DOWN" else "lr",
        canvas_bounds=root_bounds,
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        lanes=tuple(
            lane_frames[lane_id] for lane_id in lane_order if lane_id in lane_frames
        ),
        diagnostics=tuple(diagnostics),
    )

    return (
        request.result_transform(request, result)
        if request.result_transform
        else result
    )


def _edge_metadata_maps(
    *,
    request: ElkLayoutRequest,
) -> tuple[
    dict[tuple[str, str], str | None],
    dict[tuple[str, str], tuple[tuple[str, ...], bool]],
    dict[tuple[str, str], tuple[bool, str | None]],
    dict[tuple[str, str], tuple[str | None, str | None]],
    dict[tuple[str, str], tuple[str | None, str | None]],
]:
    edge_labels = {
        (edge.source_id, edge.target_id): edge.label for edge in request.edges
    }
    edge_callouts = {
        (edge.source_id, edge.target_id): (edge.callout_lines, edge.callout_near_source)
        for edge in request.edges
        if edge.callout_lines
    }
    edge_rework: dict[tuple[str, str], tuple[bool, str | None]] = {
        (edge.source_id, edge.target_id): (edge.is_rework, edge.rework_variant)
        for edge in request.edges
        if edge.is_rework or edge.rework_variant is not None
    }
    edge_tokens = {
        (edge.source_id, edge.target_id): (edge.outgoing_token, edge.incoming_token)
        for edge in request.edges
        if edge.outgoing_token is not None or edge.incoming_token is not None
    }
    edge_ports = {
        (edge.source_id, edge.target_id): (edge.source_port_side, edge.target_port_side)
        for edge in request.edges
        if edge.source_port_side is not None or edge.target_port_side is not None
    }
    return edge_labels, edge_callouts, edge_rework, edge_tokens, edge_ports


def _port_owner_map(*, request: ElkLayoutRequest) -> dict[str, str]:
    return {
        str(port["id"]): node_id
        for node_id, extras in request.serialization.node_overrides.items()
        for port in extras.get("ports", [])
    }


def execute_elk_layout(
    request: ElkLayoutRequest,
    *,
    engine: Callable[[dict[str, Any]], dict[str, Any]],
    observer: LayoutObserver | None = None,
) -> LayoutResult:
    """Run the ELK request through an injected engine boundary and normalize it."""
    payload = serialize_elk_layout_request(request)
    request_snapshot = deepcopy(payload) if observer is not None else None
    response = engine(payload)
    if not isinstance(response, dict):
        raise ElkEngineProtocolError("ELK engine must return a dictionary payload.")
    response_snapshot = deepcopy(response) if observer is not None else None
    result = normalize_elk_layout_result(response, request=request)
    errors = [
        diagnostic.message
        for diagnostic in result.diagnostics
        if diagnostic.severity == "error"
    ]
    if errors:
        raise RenderError("; ".join(errors))
    if observer is not None:
        assert request_snapshot is not None and response_snapshot is not None
        observer(
            ElkLayoutTrace(
                deepcopy(request),
                request_snapshot,
                response_snapshot,
                deepcopy(result),
            )
        )
    return result


def _collect_child_geometry(
    *,
    graph: dict[str, Any],
    parent_origin: LayoutPoint,
    node_ids: set[str],
    lane_ids: set[str],
    lane_labels: dict[str, str],
    lane_members: dict[str, tuple[str, ...]],
    node_bounds: dict[str, LayoutBounds],
    lane_frames: dict[str, LayoutLaneFrame],
    container_origins: dict[str, LayoutPoint],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> None:
    for child in graph.get("children") or []:
        if not isinstance(child, dict):
            continue
        child_id = str(child.get("id") or "")
        child_origin = LayoutPoint(
            x_px=parent_origin.x_px + _float_value(child.get("x")),
            y_px=parent_origin.y_px + _float_value(child.get("y")),
        )
        child_bounds = LayoutBounds(
            x_px=child_origin.x_px,
            y_px=child_origin.y_px,
            width_px=_float_value(child.get("width")),
            height_px=_float_value(child.get("height")),
        )
        if child_id:
            container_origins[child_id] = child_origin
        if child_id in node_ids:
            node_bounds[child_id] = child_bounds
        if child_id in lane_ids and _looks_like_lane_container(
            child,
            member_ids=lane_members.get(child_id, ()),
        ):
            lane_frames[child_id] = LayoutLaneFrame(
                id=child_id,
                label=lane_labels.get(child_id, child_id),
                bounds=child_bounds,
                node_ids=lane_members.get(child_id, ()),
            )
        _collect_child_geometry(
            graph=child,
            parent_origin=child_origin,
            node_ids=node_ids,
            lane_ids=lane_ids,
            lane_labels=lane_labels,
            lane_members=lane_members,
            node_bounds=node_bounds,
            lane_frames=lane_frames,
            container_origins=container_origins,
            diagnostics=diagnostics,
            strict=strict,
        )


def _looks_like_lane_container(
    child: dict[str, Any], *, member_ids: tuple[str, ...]
) -> bool:
    raw_children = child.get("children")
    if not isinstance(raw_children, list):
        return False
    child_ids = {
        str(raw_child.get("id") or "")
        for raw_child in raw_children
        if isinstance(raw_child, dict)
    }
    return bool(child_ids.intersection(member_ids))


def _collect_edge_geometry(
    *,
    ignored_edge_ids: set[str],
    graph: dict[str, Any],
    parent_origin: LayoutPoint,
    edge_labels: dict[tuple[str, str], str | None],
    edge_callouts: dict[tuple[str, str], tuple[tuple[str, ...], bool]],
    edge_rework: dict[tuple[str, str], tuple[bool, Any]],
    edge_tokens: dict[tuple[str, str], tuple[str | None, str | None]],
    edge_ports: dict[tuple[str, str], tuple[str | None, str | None]],
    allowed_edges: set[tuple[str, str]],
    port_owner: dict[str, str],
    container_origins: dict[str, LayoutPoint],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> None:
    for raw_edge in graph.get("edges") or []:
        if (
            isinstance(raw_edge, dict)
            and str(raw_edge.get("id") or "") in ignored_edge_ids
        ):
            continue
        routed = _route_raw_edge_path(
            raw_edge=raw_edge,
            parent_origin=parent_origin,
            edge_labels=edge_labels,
            edge_callouts=edge_callouts,
            edge_rework=edge_rework,
            edge_tokens=edge_tokens,
            edge_ports=edge_ports,
            allowed_edges=allowed_edges,
            port_owner=port_owner,
            container_origins=container_origins,
            diagnostics=diagnostics,
            strict=strict,
        )
        if routed is None:
            continue
        key, routed_path = routed
        edge_paths[key] = routed_path
    _collect_edge_geometry_from_children(
        ignored_edge_ids=ignored_edge_ids,
        graph=graph,
        parent_origin=parent_origin,
        edge_labels=edge_labels,
        edge_callouts=edge_callouts,
        edge_rework=edge_rework,
        edge_tokens=edge_tokens,
        edge_ports=edge_ports,
        allowed_edges=allowed_edges,
        port_owner=port_owner,
        container_origins=container_origins,
        edge_paths=edge_paths,
        diagnostics=diagnostics,
        strict=strict,
    )


def _route_raw_edge_path(
    *,
    raw_edge: Any,
    parent_origin: LayoutPoint,
    edge_labels: dict[tuple[str, str], str | None],
    edge_callouts: dict[tuple[str, str], tuple[tuple[str, ...], bool]],
    edge_rework: dict[tuple[str, str], tuple[bool, Any]],
    edge_tokens: dict[tuple[str, str], tuple[str | None, str | None]],
    edge_ports: dict[tuple[str, str], tuple[str | None, str | None]],
    allowed_edges: set[tuple[str, str]],
    port_owner: dict[str, str],
    container_origins: dict[str, LayoutPoint],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> tuple[tuple[str, str], RoutedEdgePath] | None:
    if not isinstance(raw_edge, dict):
        return None

    source_id, target_id = _edge_endpoints(raw_edge, port_owner=port_owner)
    if not source_id or not target_id:
        _append_diagnostic(
            diagnostics,
            code="elk-edge-endpoints-missing",
            severity=_recovery_severity(strict),
            message="ELK response contained an edge with unresolved endpoints.",
            edge_id=str(raw_edge.get("id") or ""),
        )
        return None

    edge_origin = _edge_origin(
        raw_edge,
        default_origin=parent_origin,
        container_origins=container_origins,
        diagnostics=diagnostics,
        strict=strict,
    )
    points = _edge_points(raw_edge, parent_origin=edge_origin)
    if len(points) < 2:
        _append_diagnostic(
            diagnostics,
            code="elk-edge-geometry-missing",
            severity=_recovery_severity(strict),
            message=(
                f"ELK response did not provide usable geometry for edge '{raw_edge.get('id') or ''!s}'."
            ),
            edge_id=str(raw_edge.get("id") or ""),
            source_id=source_id,
            target_id=target_id,
        )
        return None

    key = (source_id, target_id)
    if key not in allowed_edges:
        _report_unexpected_edge(
            raw_edge=raw_edge,
            source_id=source_id,
            target_id=target_id,
            diagnostics=diagnostics,
            strict=strict,
        )
        return None

    callout_lines, callout_near_source = edge_callouts.get(key, ((), False))
    is_rework, rework_variant = edge_rework.get(key, (False, None))
    outgoing_token, incoming_token = edge_tokens.get(key, (None, None))
    source_port_side, target_port_side = edge_ports.get(key, (None, None))
    label, label_point = _edge_path_label(
        raw_edge,
        fallback=edge_labels.get(key),
        parent_origin=edge_origin,
    )

    return key, RoutedEdgePath(
        edge=key,
        label=label,
        label_point=label_point,
        source_port_side=source_port_side,
        target_port_side=target_port_side,
        points=points,
        is_rework=is_rework,
        callout_lines=callout_lines,
        rework_variant=rework_variant,
        callout_near_source=callout_near_source,
        outgoing_token=outgoing_token,
        incoming_token=incoming_token,
    )


def _report_unexpected_edge(
    *,
    raw_edge: dict[str, Any],
    source_id: str,
    target_id: str,
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> None:
    _append_diagnostic(
        diagnostics,
        code="elk-edge-unexpected",
        severity=_recovery_severity(strict),
        message=(
            f"ELK response contained unexpected edge '{source_id}->{target_id}' not present in the FLO request."
        ),
        edge_id=str(raw_edge.get("id") or ""),
        source_id=source_id,
        target_id=target_id,
    )


def _collect_edge_geometry_from_children(
    *,
    ignored_edge_ids: set[str],
    graph: dict[str, Any],
    parent_origin: LayoutPoint,
    edge_labels: dict[tuple[str, str], str | None],
    edge_callouts: dict[tuple[str, str], tuple[tuple[str, ...], bool]],
    edge_rework: dict[tuple[str, str], tuple[bool, Any]],
    edge_tokens: dict[tuple[str, str], tuple[str | None, str | None]],
    edge_ports: dict[tuple[str, str], tuple[str | None, str | None]],
    allowed_edges: set[tuple[str, str]],
    port_owner: dict[str, str],
    container_origins: dict[str, LayoutPoint],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> None:
    for child in graph.get("children") or []:
        if not isinstance(child, dict):
            continue
        _collect_edge_geometry(
            ignored_edge_ids=ignored_edge_ids,
            graph=child,
            parent_origin=LayoutPoint(
                x_px=parent_origin.x_px + _float_value(child.get("x")),
                y_px=parent_origin.y_px + _float_value(child.get("y")),
            ),
            edge_labels=edge_labels,
            edge_callouts=edge_callouts,
            edge_rework=edge_rework,
            edge_tokens=edge_tokens,
            edge_ports=edge_ports,
            allowed_edges=allowed_edges,
            port_owner=port_owner,
            container_origins=container_origins,
            edge_paths=edge_paths,
            diagnostics=diagnostics,
            strict=strict,
        )


def _edge_origin(
    raw_edge: dict[str, Any],
    *,
    default_origin: LayoutPoint,
    container_origins: dict[str, LayoutPoint],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> LayoutPoint:
    container_id = str(raw_edge.get("container") or "")
    if container_id:
        origin = container_origins.get(container_id)
        if origin is not None:
            return origin
        _append_diagnostic(
            diagnostics,
            code="elk-edge-container-unknown",
            severity=_recovery_severity(strict),
            message=(
                f"ELK response referenced unknown edge container '{container_id}' for edge '{raw_edge.get('id') or ''!s}'."
            ),
            edge_id=str(raw_edge.get("id") or ""),
            container_id=container_id,
        )
        return default_origin
    return default_origin


def _finalize_layout_diagnostics(
    *,
    request: ElkLayoutRequest,
    lane_order: list[str],
    lane_frames: dict[str, LayoutLaneFrame],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    allowed_edges: set[tuple[str, str]],
    diagnostics: list[RenderDiagnostic],
    strict: bool,
) -> None:
    missing_lanes = [lane_id for lane_id in lane_order if lane_id not in lane_frames]
    for lane_id in missing_lanes:
        _append_diagnostic(
            diagnostics,
            code="elk-lane-frame-missing",
            severity=_recovery_severity(strict),
            message=f"ELK response did not produce geometry for expected lane '{lane_id}'.",
            lane_id=lane_id,
        )
    missing_edges = sorted(allowed_edges.difference(edge_paths.keys()))
    for source_id, target_id in missing_edges:
        _append_diagnostic(
            diagnostics,
            code="elk-edge-missing",
            severity=_recovery_severity(strict),
            message=f"ELK response did not normalize requested edge '{source_id}->{target_id}'.",
            source_id=source_id,
            target_id=target_id,
        )


def _recovery_severity(strict: bool) -> RenderDiagnosticSeverity:
    return "error" if strict else "warning"


def _append_diagnostic(
    diagnostics: list[RenderDiagnostic],
    *,
    code: str,
    severity: RenderDiagnosticSeverity,
    message: str,
    **metadata: Any,
) -> None:
    diagnostics.append(
        RenderDiagnostic(
            code=code,
            severity=severity,
            message=message,
            metadata={
                key: value for key, value in metadata.items() if value not in {None, ""}
            },
        )
    )


def _edge_endpoints(
    raw_edge: dict[str, Any], *, port_owner: dict[str, str]
) -> tuple[str, str]:
    sources = raw_edge.get("sources")
    targets = raw_edge.get("targets")
    source_raw = (
        str(sources[0]).strip() if isinstance(sources, list) and sources else ""
    )
    target_raw = (
        str(targets[0]).strip() if isinstance(targets, list) and targets else ""
    )
    source_id = port_owner.get(source_raw, source_raw)
    target_id = port_owner.get(target_raw, target_raw)
    return source_id, target_id


def _edge_points(
    raw_edge: dict[str, Any], *, parent_origin: LayoutPoint
) -> tuple[LayoutPoint, ...]:
    sections = raw_edge.get("sections")
    if not isinstance(sections, list):
        return ()
    points: list[LayoutPoint] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        for point in _section_points(section=section, parent_origin=parent_origin):
            if not points or points[-1] != point:
                points.append(point)
    return tuple(points)


def _section_points(
    *, section: dict[str, Any], parent_origin: LayoutPoint
) -> tuple[LayoutPoint, ...]:
    out: list[LayoutPoint] = []
    start_point = _raw_point(section.get("startPoint"), parent_origin=parent_origin)
    if start_point is not None:
        out.append(start_point)
    for raw_point in section.get("bendPoints") or []:
        point = _raw_point(raw_point, parent_origin=parent_origin)
        if point is not None:
            out.append(point)
    end_point = _raw_point(section.get("endPoint"), parent_origin=parent_origin)
    if end_point is not None:
        out.append(end_point)
    return tuple(out)


def _raw_point(raw_point: Any, *, parent_origin: LayoutPoint) -> LayoutPoint | None:
    if not isinstance(raw_point, dict):
        return None
    return LayoutPoint(
        x_px=parent_origin.x_px + _float_value(raw_point.get("x")),
        y_px=parent_origin.y_px + _float_value(raw_point.get("y")),
    )


def _edge_path_label(
    raw_edge: dict[str, Any],
    *,
    fallback: str | None,
    parent_origin: LayoutPoint,
) -> tuple[str | None, LayoutPoint | None]:
    raw_labels = raw_edge.get("labels")
    if isinstance(raw_labels, list):
        for raw_label in raw_labels:
            if not isinstance(raw_label, dict):
                continue
            text = str(raw_label.get("text") or "").strip()
            if text:
                return text, _raw_label_point(raw_label, parent_origin=parent_origin)
    return fallback, None


def _raw_label_point(
    raw_label: dict[str, Any], *, parent_origin: LayoutPoint
) -> LayoutPoint | None:
    raw_x = raw_label.get("x")
    raw_y = raw_label.get("y")
    if not isinstance(raw_x, (int, float)) or not isinstance(raw_y, (int, float)):
        return None
    raw_width = raw_label.get("width")
    raw_height = raw_label.get("height")
    width = float(raw_width) if isinstance(raw_width, (int, float)) else 0.0
    height = float(raw_height) if isinstance(raw_height, (int, float)) else 0.0
    return LayoutPoint(
        x_px=parent_origin.x_px + float(raw_x) + (width / 2.0),
        y_px=parent_origin.y_px + float(raw_y) + (height / 2.0),
    )


def _float_value(raw_value: Any) -> float:
    return float(raw_value) if isinstance(raw_value, (int, float)) else 0.0


__all__ = [
    "ElkDirection",
    "ElkLayoutEdge",
    "ElkLayoutLane",
    "ElkLayoutNode",
    "ElkLayoutRequest",
    "execute_elk_layout",
    "normalize_elk_layout_result",
    "serialize_elk_layout_request",
]
