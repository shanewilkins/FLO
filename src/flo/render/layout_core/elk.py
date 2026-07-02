"""ELK-friendly layout request API and result normalization."""

from __future__ import annotations

from dataclasses import replace
import statistics
from typing import Any, Callable

from flo.render._diagnostics import RenderDiagnostic, RenderDiagnosticSeverity
from flo.render._sppm_rework_graph import infer_rework_row_ids, translate_edge_points
from .elk_contracts import (
    ElkDirection,
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
)
from .elk_errors import ElkEngineProtocolError
from .elk_validation import validate_elk_request_namespaces
from .elk_support import (
    extract_nodes_and_edges,
    lane_specs,
    ordered_edges,
    ordered_flowchart_nodes,
    ordered_nodes,
    ordered_sppm_nodes,
    project_parent_only_subprocess_view,
    serialize_edge,
    serialize_node,
)
from .elk_sppm_helpers import (
    _node_kind_map,
    _preserves_lane_structure,
    _sppm_branch_anchor_helpers,
    _root_layout_options,
    _sppm_apply_secondary_row_edge_ports,
    _sppm_lane_direction,
    _sppm_partition_indexes_for_synthetic_rows,
    _sppm_port_id,
    _sppm_spacing_layout_options,
    _sppm_synthetic_row_lanes,
)
from .sppm_strategy import should_emit_sppm_branch_anchors
from .models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.render.options import RenderOptions
from flo.services.errors import RenderError


def build_swimlane_elk_layout_request(
    process: dict[str, Any] | Any, options: RenderOptions | None = None
) -> ElkLayoutRequest:
    """Build the first ELK layout request slice for swimlane diagrams."""
    render_options = options or RenderOptions(diagram="swimlane")
    if render_options.diagram != "swimlane":
        raise ValueError("Swimlane ELK request builder requires diagram='swimlane'.")

    nodes, edges = extract_nodes_and_edges(process)
    if render_options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)

    request = ElkLayoutRequest(
        diagram="swimlane",
        direction=_elk_direction(render_options),
        lanes=lane_specs(process=process, nodes=nodes),
        nodes=ordered_nodes(nodes),
        edges=ordered_edges(
            edges,
            node_kinds=_node_kind_map(nodes),
            diagram="swimlane",
            direction=_elk_direction(render_options),
        ),
        strict_diagnostics=render_options.layout_fit == "fit-strict",
    )
    validate_elk_request_namespaces(request)
    return request


def build_sppm_elk_layout_request(
    process: dict[str, Any] | Any, options: RenderOptions | None = None
) -> ElkLayoutRequest:
    """Build the first ELK layout request slice for SPPM diagrams."""
    render_options = options or RenderOptions(diagram="sppm")
    if render_options.diagram != "sppm":
        raise ValueError("SPPM ELK request builder requires diagram='sppm'.")

    nodes, edges = extract_nodes_and_edges(process)
    if render_options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)

    edge_specs = ordered_edges(
        edges,
        node_kinds=_node_kind_map(nodes),
        diagram="sppm",
        direction=_elk_direction(render_options),
    )
    sppm_nodes = ordered_sppm_nodes(nodes, options=render_options)
    if _preserves_lane_structure(process, nodes):
        lanes = lane_specs(process=process, nodes=nodes)
        partition_overrides: dict[str, int] = {}
    else:
        synthetic_rows = _sppm_synthetic_row_lanes(nodes=nodes, edges=edge_specs)
        lanes = ()
        partition_overrides = _sppm_partition_indexes_for_synthetic_rows(
            node_ids=[node.id for node in sppm_nodes],
            lanes=synthetic_rows,
            edges=edge_specs,
        )
        edge_specs = _sppm_apply_secondary_row_edge_ports(
            edges=edge_specs,
            synthetic_rows=synthetic_rows,
            root_direction=_elk_direction(render_options),
        )

    request = ElkLayoutRequest(
        diagram="sppm",
        direction=_elk_direction(render_options),
        lanes=lanes,
        nodes=tuple(
            replace(
                node,
                partition_index=partition_overrides.get(node.id, node.partition_index),
            )
            for node in sppm_nodes
        ),
        edges=edge_specs,
        strict_diagnostics=render_options.layout_fit == "fit-strict",
    )
    validate_elk_request_namespaces(request)
    return request


def build_flowchart_elk_layout_request(
    process: dict[str, Any] | Any, options: RenderOptions | None = None
) -> ElkLayoutRequest:
    """Build the first ELK layout request slice for flowchart diagrams."""
    render_options = options or RenderOptions(diagram="flowchart")
    if render_options.diagram != "flowchart":
        raise ValueError("Flowchart ELK request builder requires diagram='flowchart'.")

    nodes, edges = extract_nodes_and_edges(process)
    if render_options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)

    request = ElkLayoutRequest(
        diagram="flowchart",
        direction=_elk_direction(render_options),
        lanes=(),
        nodes=ordered_flowchart_nodes(nodes),
        edges=ordered_edges(
            edges,
            node_kinds=_node_kind_map(nodes),
            diagram="flowchart",
            direction=_elk_direction(render_options),
        ),
        strict_diagnostics=render_options.layout_fit == "fit-strict",
    )
    validate_elk_request_namespaces(request)
    return request


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
    if request.diagram == "sppm":
        _balance_sppm_queue_task_gaps(
            request=request,
            node_bounds=node_bounds,
            edge_paths=edge_paths,
        )
        _normalize_sppm_mainline_horizontal_spacing(
            request=request,
            node_bounds=node_bounds,
            edge_paths=edge_paths,
        )

    return LayoutResult(
        orientation="tb" if request.direction == "DOWN" else "lr",
        canvas_bounds=root_bounds,
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        lanes=tuple(
            lane_frames[lane_id] for lane_id in lane_order if lane_id in lane_frames
        ),
        diagnostics=tuple(diagnostics),
    )


def _balance_sppm_queue_task_gaps(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> None:
    node_ids = set(node_bounds)
    mainline_ids, _rework_ids = _infer_sppm_row_ids_from_request(
        request=request,
        node_ids=node_ids,
    )
    if len(mainline_ids) < 3:
        return

    node_kind_by_id = {node.id: str(node.kind or "").lower() for node in request.nodes}
    direct_edges = {
        (edge.source_id, edge.target_id) for edge in request.edges if not edge.is_rework
    }

    incoming_by_target, outgoing_by_source = _mainline_direct_adjacency(
        mainline_ids=mainline_ids,
        direct_edges=direct_edges,
    )

    shifts: dict[str, tuple[float, float]] = {}

    def _is_queue(node_id: str) -> bool:
        return _is_queue_node(node_id=node_id, node_kind_by_id=node_kind_by_id)

    for queue_id in sorted(mainline_ids, key=lambda node_id: node_bounds[node_id].x_px):
        if not _is_queue(queue_id):
            continue
        incoming = incoming_by_target.get(queue_id, [])
        outgoing = outgoing_by_source.get(queue_id, [])
        shift = _queue_gap_shift(
            queue_id=queue_id,
            incoming=incoming,
            outgoing=outgoing,
            node_bounds=node_bounds,
            is_queue=_is_queue,
        )
        if shift is not None:
            shifts[queue_id] = (shift, 0.0)

    if not shifts:
        return

    _apply_layout_shifts(
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        shifts=shifts,
    )


def _is_queue_node(*, node_id: str, node_kind_by_id: dict[str, str]) -> bool:
    kind = str(node_kind_by_id.get(node_id, "")).lower()
    return kind == "queue" if kind else ("queue" in node_id.lower())


def _mainline_direct_adjacency(
    *,
    mainline_ids: set[str],
    direct_edges: set[tuple[str, str]],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    incoming_by_target: dict[str, list[str]] = {node_id: [] for node_id in mainline_ids}
    outgoing_by_source: dict[str, list[str]] = {node_id: [] for node_id in mainline_ids}
    for source_id, target_id in direct_edges:
        if source_id not in mainline_ids or target_id not in mainline_ids:
            continue
        incoming_by_target[target_id].append(source_id)
        outgoing_by_source[source_id].append(target_id)
    return incoming_by_target, outgoing_by_source


def _queue_gap_shift(
    *,
    queue_id: str,
    incoming: list[str],
    outgoing: list[str],
    node_bounds: dict[str, LayoutBounds],
    is_queue: Callable[[str], bool],
) -> float | None:
    if len(incoming) != 1 or len(outgoing) != 1:
        return None

    upstream_id = incoming[0]
    downstream_id = outgoing[0]
    if not is_queue(upstream_id) or is_queue(downstream_id):
        return None
    if upstream_id not in node_bounds or downstream_id not in node_bounds:
        return None

    upstream_right = node_bounds[upstream_id].x_px + node_bounds[upstream_id].width_px
    queue_left = node_bounds[queue_id].x_px
    queue_width = node_bounds[queue_id].width_px
    downstream_left = node_bounds[downstream_id].x_px

    gap_left = queue_left - upstream_right
    gap_right = downstream_left - (queue_left + queue_width)
    if gap_left <= 0.0 or gap_right <= 0.0:
        return None
    if gap_right <= (gap_left * 1.6):
        return None

    target_queue_left = (downstream_left + upstream_right - queue_width) / 2.0
    min_gap_px = 56.0
    target_queue_left = max(target_queue_left, upstream_right + min_gap_px)
    target_queue_left = min(
        target_queue_left,
        downstream_left - queue_width - min_gap_px,
    )
    if target_queue_left <= upstream_right:
        return None
    if target_queue_left + queue_width >= downstream_left:
        return None
    return target_queue_left - queue_left


def _normalize_sppm_mainline_horizontal_spacing(
    *,
    request: ElkLayoutRequest,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> None:
    mainline_ids, _rework_ids = _infer_sppm_row_ids_from_request(
        request=request,
        node_ids=set(node_bounds),
    )
    ordered = sorted(mainline_ids, key=lambda node_id: node_bounds[node_id].x_px)
    if len(ordered) < 3:
        return

    gaps: list[float] = []
    for left_id, right_id in zip(ordered, ordered[1:]):
        left_bounds = node_bounds[left_id]
        right_bounds = node_bounds[right_id]
        gap = right_bounds.x_px - (left_bounds.x_px + left_bounds.width_px)
        if gap > 0.0:
            gaps.append(gap)
    if len(gaps) < 2:
        return

    target_gap = max(56.0, float(statistics.median(gaps)))
    if max(gaps) <= (target_gap * 1.25) and min(gaps) >= (target_gap * 0.75):
        return

    shifts: dict[str, tuple[float, float]] = {}
    propagated_dx = 0.0
    for left_id, right_id in zip(ordered, ordered[1:]):
        left_dx = shifts.get(left_id, (0.0, 0.0))[0]
        right_dx, right_dy = shifts.get(right_id, (0.0, 0.0))
        left_right = node_bounds[left_id].x_px + left_dx + node_bounds[left_id].width_px
        right_left = node_bounds[right_id].x_px + right_dx + propagated_dx
        propagated_dx += (left_right + target_gap) - right_left
        shifts[right_id] = (right_dx + propagated_dx, right_dy)

    _apply_layout_shifts(
        node_bounds=node_bounds,
        edge_paths=edge_paths,
        shifts=shifts,
    )


def _apply_layout_shifts(
    *,
    node_bounds: dict[str, LayoutBounds],
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
    shifts: dict[str, tuple[float, float]],
) -> None:
    if not shifts:
        return

    for node_id, (dx, dy) in shifts.items():
        bounds = node_bounds[node_id]
        node_bounds[node_id] = LayoutBounds(
            x_px=bounds.x_px + dx,
            y_px=bounds.y_px + dy,
            width_px=bounds.width_px,
            height_px=bounds.height_px,
        )

    for edge_key, edge_path in tuple(edge_paths.items()):
        source_id, target_id = edge_key
        source_shift = shifts.get(source_id, (0.0, 0.0))
        target_shift = shifts.get(target_id, (0.0, 0.0))
        if source_shift == (0.0, 0.0) and target_shift == (0.0, 0.0):
            continue
        shifted_label_point = edge_path.label_point
        if shifted_label_point is not None:
            lx = shifted_label_point.x_px + ((source_shift[0] + target_shift[0]) / 2.0)
            ly = shifted_label_point.y_px + ((source_shift[1] + target_shift[1]) / 2.0)
            shifted_label_point = LayoutPoint(x_px=lx, y_px=ly)
        edge_paths[edge_key] = replace(
            edge_path,
            points=translate_edge_points(
                edge_path.points,
                source_shift=source_shift,
                target_shift=target_shift,
            ),
            label_point=shifted_label_point,
        )


def _infer_sppm_row_ids_from_request(
    *,
    request: ElkLayoutRequest,
    node_ids: set[str],
) -> tuple[set[str], set[str]]:
    return infer_rework_row_ids(
        node_ids=node_ids,
        edges=(
            (
                edge.source_id,
                edge.target_id,
                edge.is_rework,
                edge.rework_variant,
            )
            for edge in request.edges
        ),
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
    edge_rework = {
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
        _sppm_port_id(node.id, side): node.id
        for node in request.nodes
        for side in ("NORTH", "EAST", "SOUTH", "WEST")
    }


def serialize_elk_layout_request(request: ElkLayoutRequest) -> dict[str, Any]:
    """Lower a FLO-owned ELK request into an ELK-shaped payload."""
    node_by_id = {node.id: node for node in request.nodes}
    helper_nodes: list[dict[str, Any]] = []
    helper_edges: list[dict[str, Any]] = []

    if request.diagram == "sppm" and should_emit_sppm_branch_anchors(
        has_lanes=bool(request.lanes)
    ):
        helper_nodes, helper_edges = _sppm_branch_anchor_helpers(request=request)

    children = _serialize_lane_children(request=request, node_by_id=node_by_id)

    assigned_node_ids = {
        node_id
        for lane in request.lanes
        for node_id in lane.node_ids
        if node_id in node_by_id
    }
    children.extend(
        _serialize_unassigned_nodes(
            request=request,
            assigned_node_ids=assigned_node_ids,
        )
    )

    if helper_nodes:
        children.extend(helper_nodes)

    serialized_edges = _serialize_request_edges(
        request=request, helper_edges=helper_edges
    )

    return {
        "id": f"flo:{request.diagram}",
        "layoutOptions": _root_layout_options(request),
        "children": children,
        "edges": serialized_edges,
    }


def _serialize_lane_children(
    *,
    request: ElkLayoutRequest,
    node_by_id: dict[str, ElkLayoutNode],
) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    for lane_index, lane in enumerate(request.lanes):
        lane_layout_options: dict[str, str] = {
            "elk.partitioning.partition": str(lane_index)
        }
        if request.diagram == "sppm":
            lane_layout_options.update(
                {
                    "elk.algorithm": "layered",
                    "elk.direction": _sppm_lane_direction(
                        lane_id=lane.id,
                        root_direction=request.direction,
                    ),
                    "elk.edgeRouting": "ORTHOGONAL",
                    **_sppm_spacing_layout_options(),
                    "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
                    "elk.layered.nodePlacement.bk.fixedAlignment": "TOP",
                }
            )
        children.append(
            {
                "id": lane.id,
                "labels": [{"text": lane.label}],
                "layoutOptions": lane_layout_options,
                "children": [
                    serialize_node(node_by_id[node_id], diagram=request.diagram)
                    for node_id in lane.node_ids
                    if node_id in node_by_id
                ],
            }
        )
    return children


def _serialize_unassigned_nodes(
    *,
    request: ElkLayoutRequest,
    assigned_node_ids: set[str],
) -> list[dict[str, Any]]:
    return [
        serialize_node(node, diagram=request.diagram)
        for node in request.nodes
        if node.id not in assigned_node_ids
    ]


def _serialize_request_edges(
    *,
    request: ElkLayoutRequest,
    helper_edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    serialized_edges = [
        serialize_edge(edge, diagram=request.diagram) for edge in request.edges
    ]
    if helper_edges:
        serialized_edges.extend(helper_edges)
    return serialized_edges


def execute_elk_layout(
    request: ElkLayoutRequest,
    *,
    engine: Callable[[dict[str, Any]], dict[str, Any]],
) -> LayoutResult:
    """Run the ELK request through an injected engine boundary and normalize it."""
    response = engine(serialize_elk_layout_request(request))
    if not isinstance(response, dict):
        raise ElkEngineProtocolError("ELK engine must return a dictionary payload.")
    result = normalize_elk_layout_result(response, request=request)
    errors = [
        diagnostic.message
        for diagnostic in result.diagnostics
        if diagnostic.severity == "error"
    ]
    if errors:
        raise RenderError("; ".join(errors))
    return result


def _elk_direction(options: RenderOptions) -> ElkDirection:
    return "DOWN" if options.orientation == "tb" else "RIGHT"


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
                f"ELK response did not provide usable geometry for edge '{str(raw_edge.get('id') or '')}'."
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
    if str(raw_edge.get("id") or "").startswith("__sppm_helper_"):
        return
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
                f"ELK response referenced unknown edge container '{container_id}' for edge '{str(raw_edge.get('id') or '')}'."
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
    "build_flowchart_elk_layout_request",
    "build_sppm_elk_layout_request",
    "build_swimlane_elk_layout_request",
    "execute_elk_layout",
    "normalize_elk_layout_result",
    "serialize_elk_layout_request",
]
