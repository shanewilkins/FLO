"""ELK-friendly layout request API and result normalization."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from .elk_contracts import (
    ElkDirection,
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
)
from .elk_errors import ElkEngineProtocolError
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
from .models import (
    LayoutBounds,
    LayoutLaneFrame,
    LayoutPoint,
    LayoutResult,
    RoutedEdgePath,
)
from flo.render.options import RenderOptions


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

    return ElkLayoutRequest(
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
    )


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

    return ElkLayoutRequest(
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
    )


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

    return ElkLayoutRequest(
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
    )


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

    node_bounds: dict[str, LayoutBounds] = {}
    lane_frames: dict[str, LayoutLaneFrame] = {}
    _collect_child_geometry(
        graph=payload,
        parent_origin=LayoutPoint(x_px=root_bounds.x_px, y_px=root_bounds.y_px),
        node_ids=node_ids,
        lane_ids=set(lane_order),
        lane_labels=lane_labels,
        lane_members=lane_members,
        node_bounds=node_bounds,
        lane_frames=lane_frames,
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
    children: list[dict[str, Any]] = []
    helper_nodes: list[dict[str, Any]] = []
    helper_edges: list[dict[str, Any]] = []

    if request.diagram == "sppm":
        helper_nodes, helper_edges = _sppm_branch_anchor_helpers(request=request)

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

    assigned_node_ids = {
        node_id
        for lane in request.lanes
        for node_id in lane.node_ids
        if node_id in node_by_id
    }
    for node in request.nodes:
        if node.id in assigned_node_ids:
            continue
        children.append(serialize_node(node, diagram=request.diagram))

    if helper_nodes:
        children.extend(helper_nodes)

    serialized_edges = [
        serialize_edge(edge, diagram=request.diagram) for edge in request.edges
    ]
    if helper_edges:
        serialized_edges.extend(helper_edges)

    return {
        "id": f"flo:{request.diagram}",
        "layoutOptions": _root_layout_options(request),
        "children": children,
        "edges": serialized_edges,
    }


def execute_elk_layout(
    request: ElkLayoutRequest,
    *,
    engine: Callable[[dict[str, Any]], dict[str, Any]],
) -> LayoutResult:
    """Run the ELK request through an injected engine boundary and normalize it."""
    response = engine(serialize_elk_layout_request(request))
    if not isinstance(response, dict):
        raise ElkEngineProtocolError("ELK engine must return a dictionary payload.")
    return normalize_elk_layout_result(response, request=request)


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
        if child_id in node_ids:
            node_bounds[child_id] = child_bounds
        if child_id in lane_ids:
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
        )


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
    edge_paths: dict[tuple[str, str], RoutedEdgePath],
) -> None:
    for raw_edge in graph.get("edges") or []:
        if not isinstance(raw_edge, dict):
            continue
        source_id, target_id = _edge_endpoints(raw_edge, port_owner=port_owner)
        if not source_id or not target_id:
            continue
        points = _edge_points(raw_edge, parent_origin=parent_origin)
        if len(points) < 2:
            continue
        key = (source_id, target_id)
        if key not in allowed_edges:
            continue
        callout_lines, callout_near_source = edge_callouts.get(key, ((), False))
        is_rework, rework_variant = edge_rework.get(key, (False, None))
        outgoing_token, incoming_token = edge_tokens.get(key, (None, None))
        source_port_side, target_port_side = edge_ports.get(key, (None, None))
        label, label_point = _edge_path_label(
            raw_edge,
            fallback=edge_labels.get(key),
            parent_origin=parent_origin,
        )
        edge_paths[key] = RoutedEdgePath(
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
    for child in graph.get("children") or []:
        if isinstance(child, dict):
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
                edge_paths=edge_paths,
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
