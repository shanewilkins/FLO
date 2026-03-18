"""Graphviz DOT renderers for FLO models."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from flo.compiler.analysis import (
    infer_material_movements,
    aggregate_material_movements,
    infer_people_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
)

from .options import RenderOptions


def render_flowchart_dot(process: Dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a simple flowchart DOT representation.

    Supports canonical IR objects and dict-based shapes.
    """
    return _render_dot_graph(process, options=options or RenderOptions(), use_swimlanes=False)


def render_swimlane_dot(process: Dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a swimlane-style DOT graph.

    Swimlane mode groups nodes by lane in cluster subgraphs.
    """
    render_options = options or RenderOptions(diagram="swimlane")
    return _render_dot_graph(process, options=render_options, use_swimlanes=True)


def render_spaghetti_dot(process: Dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a spaghetti-map style DOT graph from inferred movements."""
    return _render_spaghetti_graph(process, options=options or RenderOptions(diagram="spaghetti"))


def _render_spaghetti_graph(process: Dict[str, Any] | Any, options: RenderOptions) -> str:
    material_movements = infer_material_movements(process)
    people_movements = infer_people_movements(process)
    material_routes = aggregate_material_movements(material_movements)
    people_routes = _spaghetti_people_routes(people_movements=people_movements, options=options)
    locations = extract_location_spatial_index(process)
    include_material, include_people = _spaghetti_channels(options)

    routes_for_locations: list[dict[str, Any]] = []
    if include_material:
        routes_for_locations.extend(material_routes)
    if include_people:
        routes_for_locations.extend(people_routes)

    lines: list[str] = _spaghetti_graph_prelude()
    _append_spaghetti_boundary(lines=lines, process=process)
    _append_spaghetti_location_nodes(
        lines=lines,
        locations=locations,
        location_ids=_ordered_location_ids(locations=locations, routes=routes_for_locations),
    )
    if include_material:
        _append_spaghetti_route_edges(lines=lines, routes=material_routes, options=options, channel="material")
    if include_people:
        _append_spaghetti_route_edges(lines=lines, routes=people_routes, options=options, channel="people")

    lines.append("}")
    return "\n".join(lines)


def _spaghetti_graph_prelude() -> list[str]:
    return [
        "digraph {",
        "  graph [layout=neato, overlap=false, splines=true, outputorder=edgesfirst];",
        "  node [shape=circle, fontname=Helvetica, style=filled, fillcolor=aliceblue, color=steelblue4];",
        "  edge [fontname=Helvetica, arrowsize=0.8];",
    ]


def _append_spaghetti_location_nodes(
    lines: list[str],
    locations: dict[str, dict[str, Any]],
    location_ids: list[str],
) -> None:
    for location_id in location_ids:
        info = locations.get(location_id, {})
        node_attrs = _spaghetti_location_node_attrs(location_id=location_id, info=info)
        lines.append(f'  "{_escape(location_id)}" [{", ".join(node_attrs)}];')


def _append_spaghetti_boundary(lines: list[str], process: Dict[str, Any] | Any) -> None:
    boundary = _extract_spaghetti_boundary(process)
    if boundary is None:
        return

    raw_points = boundary.get("points")
    if not isinstance(raw_points, list):
        return

    points: list[tuple[float, float]] = []
    for raw_point in raw_points:
        if not isinstance(raw_point, tuple) or len(raw_point) != 2:
            continue
        x_value = raw_point[0]
        y_value = raw_point[1]
        if not isinstance(x_value, (int, float)) or isinstance(x_value, bool):
            continue
        if not isinstance(y_value, (int, float)) or isinstance(y_value, bool):
            continue
        points.append((float(x_value), float(y_value)))

    if len(points) < 3:
        return

    point_ids: list[str] = []
    for index, point in enumerate(points):
        x, y = point
        point_id = f"__facility_boundary_{index}"
        point_ids.append(point_id)
        lines.append(
            '  "{point_id}" [label="", shape=point, width=0.01, height=0.01, style=invis, pos="{x:.3f},{y:.3f}!", pin=true];'.format(
                point_id=point_id,
                x=float(x),
                y=float(y),
            )
        )

    if len(point_ids) < 3:
        return

    ring = [*point_ids, point_ids[0]]
    for source, target in zip(ring, ring[1:]):
        lines.append(
            f'  "{source}" -> "{target}" [dir=none, color=gray60, style=dashed, penwidth=1.2, constraint=false, weight=0];'
        )

    label = _boundary_label(boundary)
    if label:
        centroid_x, centroid_y = _boundary_centroid(points)
        lines.append(
            '  "__facility_boundary_label" [label="{label}", shape=plaintext, fontcolor=gray40, fontsize=11, pos="{x:.3f},{y:.3f}!", pin=true];'.format(
                label=_escape(label),
                x=centroid_x,
                y=centroid_y,
            )
        )


def _extract_spaghetti_boundary(process: Dict[str, Any] | Any) -> dict[str, Any] | None:
    process_metadata = _extract_process_metadata(process)
    boundary_candidate = _extract_boundary_candidate(process_metadata)
    points = _boundary_points(boundary_candidate)
    if len(points) < 3:
        return None

    boundary: dict[str, Any] = {"points": points}
    if isinstance(boundary_candidate, dict):
        boundary["name"] = boundary_candidate.get("name")
        boundary["label"] = boundary_candidate.get("label")
    return boundary


def _extract_process_metadata(process: Dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(process, "process_metadata"):
        metadata = getattr(process, "process_metadata", None)
        return metadata if isinstance(metadata, dict) else {}

    if isinstance(process, dict):
        proc = process.get("process")
        if isinstance(proc, dict):
            metadata = proc.get("metadata")
            return metadata if isinstance(metadata, dict) else {}
    return {}


def _extract_boundary_candidate(process_metadata: dict[str, Any]) -> Any:
    for key in ("layout_boundary", "boundary", "area_boundary"):
        if key in process_metadata:
            return process_metadata.get(key)

    layout = process_metadata.get("layout")
    if isinstance(layout, dict) and "boundary" in layout:
        return layout.get("boundary")
    return None


def _boundary_points(boundary: Any) -> list[tuple[float, float]]:
    if boundary is None:
        return []
    if isinstance(boundary, list):
        return _parse_boundary_points(boundary)
    if not isinstance(boundary, dict):
        return []

    points = _parse_boundary_points(boundary.get("points"))
    if points:
        return points

    vertices = _parse_boundary_points(boundary.get("vertices"))
    if vertices:
        return vertices

    return _rectangle_boundary_points(boundary)


def _parse_boundary_points(raw_points: Any) -> list[tuple[float, float]]:
    if not isinstance(raw_points, list):
        return []
    points: list[tuple[float, float]] = []
    for raw_point in raw_points:
        if not isinstance(raw_point, dict):
            continue
        x = _as_number(raw_point.get("x"))
        y = _as_number(raw_point.get("y"))
        if x is None or y is None:
            continue
        points.append((x, y))
    return points


def _rectangle_boundary_points(boundary: dict[str, Any]) -> list[tuple[float, float]]:
    bounds = _rectangle_bounds(boundary)
    if bounds is None:
        return []
    min_x, min_y, max_x, max_y = bounds
    return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]


def _rectangle_bounds(boundary: dict[str, Any]) -> tuple[float, float, float, float] | None:
    min_max = _coerced_bounds(
        min_x=boundary.get("min_x"),
        min_y=boundary.get("min_y"),
        max_x=boundary.get("max_x"),
        max_y=boundary.get("max_y"),
    )
    if min_max is not None:
        return min_max

    left_right = _coerced_bounds(
        min_x=boundary.get("left"),
        min_y=boundary.get("bottom"),
        max_x=boundary.get("right"),
        max_y=boundary.get("top"),
    )
    if left_right is not None:
        return left_right

    origin_x = _as_number(boundary.get("x"))
    origin_y = _as_number(boundary.get("y"))
    width = _as_number(boundary.get("width"))
    height = _as_number(boundary.get("height"))
    if origin_x is None or origin_y is None or width is None or height is None:
        return None
    if width <= 0 or height <= 0:
        return None
    return origin_x, origin_y, origin_x + width, origin_y + height


def _coerced_bounds(min_x: Any, min_y: Any, max_x: Any, max_y: Any) -> tuple[float, float, float, float] | None:
    x0 = _as_number(min_x)
    y0 = _as_number(min_y)
    x1 = _as_number(max_x)
    y1 = _as_number(max_y)
    if x0 is None or y0 is None or x1 is None or y1 is None:
        return None
    if x0 == x1 or y0 == y1:
        return None
    min_x_val = min(x0, x1)
    max_x_val = max(x0, x1)
    min_y_val = min(y0, y1)
    max_y_val = max(y0, y1)
    return min_x_val, min_y_val, max_x_val, max_y_val


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _boundary_label(boundary: dict[str, Any]) -> str | None:
    for key in ("label", "name"):
        value = boundary.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _boundary_centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    if not points:
        return 0.0, 0.0
    x_sum = sum(point[0] for point in points)
    y_sum = sum(point[1] for point in points)
    count = float(len(points))
    return x_sum / count, y_sum / count


def _spaghetti_location_node_attrs(location_id: str, info: dict[str, Any]) -> list[str]:
    label = str(info.get("name") or location_id)
    node_attrs = [f'label="{_escape(label)}"']
    x = info.get("x")
    y = info.get("y")
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        node_attrs.append(f'pos="{float(x):.3f},{float(y):.3f}!"')
        node_attrs.append("pin=true")
    return node_attrs


def _append_spaghetti_route_edges(
    lines: list[str],
    routes: list[dict[str, Any]],
    options: RenderOptions,
    channel: str,
) -> None:
    for route in routes:
        edge_line = _spaghetti_route_edge_line(route=route, options=options, channel=channel)
        if edge_line is None:
            continue
        lines.append(edge_line)


def _spaghetti_route_edge_line(route: dict[str, Any], options: RenderOptions, channel: str) -> str | None:
    source = str(route.get("from_location") or "")
    target = str(route.get("to_location") or "")
    if not source or not target:
        return None

    count = int(route.get("count") or 0)
    penwidth = min(6.0, 1.0 + (0.7 * max(1, count)))
    edge_attrs = [
        f"penwidth={penwidth:.2f}",
        f'xlabel="{_spaghetti_channel_xlabel(channel=channel, route=route, count=count, options=options)}"',
        *_spaghetti_channel_edge_attrs(channel=channel, route=route, options=options),
    ]

    distance_label = _spaghetti_distance_label(route)
    if distance_label is not None:
        edge_attrs.append(distance_label)

    if options.detail == "verbose":
        taillabel = _spaghetti_route_entities_taillabel(route=route, channel=channel)
        if taillabel is not None:
            edge_attrs.append(taillabel)

    return f'  "{_escape(source)}" -> "{_escape(target)}" [{", ".join(edge_attrs)}];'


def _spaghetti_distance_label(route: dict[str, Any]) -> str | None:
    distance = route.get("distance")
    if not isinstance(distance, dict):
        return None
    value = distance.get("value")
    unit = distance.get("unit")
    if not isinstance(value, (int, float)) or not unit:
        return None
    return f'label="{float(value):.2f} {str(unit)}"'


def _spaghetti_route_entities_taillabel(route: dict[str, Any], channel: str) -> str | None:
    entities_key = "items" if channel == "material" else "workers"
    entities = route.get(entities_key) if isinstance(route.get(entities_key), list) else []
    if not entities:
        return None
    label_prefix = "items" if channel == "material" else "workers"
    return f'taillabel="{_escape(label_prefix + ": " + ", ".join(str(item) for item in entities))}"'


def _spaghetti_channels(options: RenderOptions) -> tuple[bool, bool]:
    channel = str(options.spaghetti_channel or "both")
    if channel == "material":
        return True, False
    if channel == "people":
        return False, True
    return True, True


def _spaghetti_people_mode(options: RenderOptions) -> str:
    mode = str(options.spaghetti_people_mode or "aggregate")
    if mode == "worker":
        return "worker"
    return "aggregate"


def _spaghetti_people_routes(people_movements: list[dict[str, Any]], options: RenderOptions) -> list[dict[str, Any]]:
    if _spaghetti_people_mode(options) == "worker":
        return aggregate_people_movements_by_worker(people_movements)
    return aggregate_people_movements(people_movements)


def _spaghetti_channel_xlabel(channel: str, route: dict[str, Any], count: int, options: RenderOptions) -> str:
    if channel != "people":
        return f"M {count}x"

    worker = _spaghetti_primary_worker(route)
    if _spaghetti_people_mode(options) == "worker" and worker:
        return f"P {worker} {count}x"
    return f"P {count}x"


def _spaghetti_channel_edge_attrs(channel: str, route: dict[str, Any], options: RenderOptions) -> list[str]:
    if channel != "people":
        return ["color=tomato4", "fontcolor=tomato4"]

    if _spaghetti_people_mode(options) == "aggregate":
        return ["color=royalblue4", "style=dashed", "fontcolor=royalblue4"]

    worker = _spaghetti_primary_worker(route)
    if not worker:
        return ["color=royalblue4", "style=dashed", "fontcolor=royalblue4"]

    color, style = _spaghetti_worker_style(worker)
    return [f"color={color}", f"style={style}", f"fontcolor={color}"]


def _spaghetti_primary_worker(route: dict[str, Any]) -> str | None:
    workers = route.get("workers") if isinstance(route.get("workers"), list) else []
    if not workers:
        return None
    worker = str(workers[0]).strip()
    return worker or None


def _spaghetti_worker_style(worker: str) -> tuple[str, str]:
    palette: list[tuple[str, str]] = [
        ("royalblue4", "dashed"),
        ("forestgreen", "dotted"),
        ("darkorange3", "solid"),
        ("firebrick3", "bold"),
        ("purple4", "dashed"),
        ("deepskyblue4", "dotted"),
        ("sienna4", "solid"),
        ("darkgoldenrod4", "bold"),
    ]
    index = _stable_palette_index(worker, len(palette))
    return palette[index]


def _stable_palette_index(text: str, size: int) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big", signed=False)
    return seed % max(1, size)


def _ordered_location_ids(locations: dict[str, dict[str, Any]], routes: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    for location_id in sorted(locations.keys()):
        seen.add(location_id)
        ordered.append(location_id)

    for route in routes:
        for key in ("from_location", "to_location"):
            location_id = str(route.get(key) or "")
            if not location_id or location_id in seen:
                continue
            seen.add(location_id)
            ordered.append(location_id)

    return ordered


def _render_dot_graph(process: Dict[str, Any] | Any, options: RenderOptions, use_swimlanes: bool) -> str:
    nodes, edges = _extract_nodes_and_edges(process)
    if options.subprocess_view == "parent_only":
        nodes, edges = _project_parent_only_subprocess_view(nodes, edges)
    node_lanes = _node_lane_map(nodes)
    rankdir = "TB" if options.orientation == "tb" else "LR"

    lines: list[str] = ["digraph {"]
    lines.append(f"  rankdir={rankdir};")
    lines.append("  graph [compound=true, newrank=true, nodesep=0.7, ranksep=0.9, splines=true];")
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    if use_swimlanes:
        _append_swimlane_nodes(lines=lines, nodes=nodes, options=options)
    else:
        _append_flowchart_nodes(lines=lines, nodes=nodes, options=options)

    _append_edges(lines=lines, edges=edges, options=options, use_swimlanes=use_swimlanes, node_lanes=node_lanes)

    lines.append("}")
    return "\n".join(lines)


def _project_parent_only_subprocess_view(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hidden_ids, visible_ids, visible_nodes = _partition_subprocess_view_nodes(nodes)

    if not hidden_ids:
        return nodes, edges
    outgoing = _index_outgoing_edges(edges)
    collapsed_edges = _collapse_parent_only_edges(
        visible_ids=visible_ids,
        hidden_ids=hidden_ids,
        outgoing=outgoing,
    )
    return visible_nodes, collapsed_edges


def _partition_subprocess_view_nodes(
    nodes: list[dict[str, Any]],
) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    hidden_ids: set[str] = set()
    visible_ids: set[str] = set()

    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        if _subprocess_parent(node):
            hidden_ids.add(node_id)
        else:
            visible_ids.add(node_id)

    visible_nodes = [
        node
        for node in nodes
        if (node_id := str(node.get("id") or "")) and node_id in visible_ids
    ]
    return hidden_ids, visible_ids, visible_nodes


def _index_outgoing_edges(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        outgoing.setdefault(source, []).append(edge)
    return outgoing


def _collapse_parent_only_edges(
    visible_ids: set[str],
    hidden_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    collapsed_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None]] = set()

    for source in visible_ids:
        for edge in outgoing.get(source, []):
            target = str(edge.get("target") or "")
            if not target:
                continue

            branch_label = _edge_branch_label(edge)
            if target in visible_ids:
                _add_collapsed_edge(
                    collapsed_edges=collapsed_edges,
                    seen_edges=seen_edges,
                    source=source,
                    target=target,
                    branch_label=branch_label,
                )
                continue
            if target not in hidden_ids:
                continue

            for nested_target, next_label in _visible_targets_through_hidden(
                start_hidden=target,
                initial_label=branch_label,
                hidden_ids=hidden_ids,
                visible_ids=visible_ids,
                outgoing=outgoing,
            ):
                _add_collapsed_edge(
                    collapsed_edges=collapsed_edges,
                    seen_edges=seen_edges,
                    source=source,
                    target=nested_target,
                    branch_label=next_label,
                )

    return collapsed_edges


def _add_collapsed_edge(
    collapsed_edges: list[dict[str, Any]],
    seen_edges: set[tuple[str, str, str | None]],
    source: str,
    target: str,
    branch_label: str | None,
) -> None:
    if source == target:
        return
    edge_key = (source, target, branch_label)
    if edge_key in seen_edges:
        return
    seen_edges.add(edge_key)

    edge: dict[str, Any] = {"source": source, "target": target}
    if branch_label is not None:
        edge["label"] = branch_label
    collapsed_edges.append(edge)


def _visible_targets_through_hidden(
    start_hidden: str,
    initial_label: str | None,
    hidden_ids: set[str],
    visible_ids: set[str],
    outgoing: dict[str, list[dict[str, Any]]],
) -> list[tuple[str, str | None]]:
    targets: list[tuple[str, str | None]] = []
    pending: list[tuple[str, str | None]] = [(start_hidden, initial_label)]
    visited_hidden: set[tuple[str, str | None]] = set()

    while pending:
        hidden_id, active_label = pending.pop()
        hidden_state = (hidden_id, active_label)
        if hidden_state in visited_hidden:
            continue
        visited_hidden.add(hidden_state)

        for nested_edge in outgoing.get(hidden_id, []):
            nested_target = str(nested_edge.get("target") or "")
            if not nested_target:
                continue

            next_label = active_label or _edge_branch_label(nested_edge)
            if nested_target in visible_ids:
                targets.append((nested_target, next_label))
            elif nested_target in hidden_ids:
                pending.append((nested_target, next_label))

    return targets


def _edge_branch_label(edge: dict[str, Any]) -> str | None:
    outcome = edge.get("outcome")
    if outcome is not None:
        text = str(outcome).strip()
        return text or None

    label = edge.get("label")
    if label is not None:
        text = str(label).strip()
        return text or None

    return None


def _append_swimlane_nodes(lines: list[str], nodes: list[dict[str, Any]], options: RenderOptions) -> None:
    lane_groups, unlaned_nodes = _partition_nodes_by_lane(nodes)
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id:
            nodes_by_id[node_id] = node

    children_by_parent = _subprocess_children_map(nodes, nodes_by_id)

    lane_specs = [(lane_name, lane_nodes, _safe_cluster_id(lane_name)) for lane_name, lane_nodes in lane_groups.items()]
    if unlaned_nodes:
        lane_specs.append(("unassigned", unlaned_nodes, "unassigned"))

    left_boundary_nodes: list[str] = []
    right_boundary_nodes: list[str] = []

    for lane_index, (lane_name, lane_nodes, lane_id) in enumerate(lane_specs):
        left_anchor = f"__lane_{lane_id}_left"
        right_anchor = f"__lane_{lane_id}_right"
        left_boundary_nodes.append(left_anchor)
        right_boundary_nodes.append(right_anchor)

        lines.append(f"  subgraph cluster_{lane_id} {{")
        lines.append(f'    label="{_escape(str(lane_name))}";')
        lines.append("    style=\"rounded,filled\";")
        lines.append("    penwidth=2;")
        lines.append("    color=gray55;")
        lines.append(f'    fillcolor="{_lane_fillcolor(lane_index)}";')
        lines.append("    labelloc=t;")
        lines.append("    labeljust=l;")
        lines.append(f'    "{left_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')
        lines.append(f'    "{right_anchor}" [label="", shape=point, width=0.01, height=0.01, style=invis];')

        _append_swimlane_lane_nodes(
            lines=lines,
            lane_nodes=lane_nodes,
            children_by_parent=children_by_parent,
            options=options,
        )

        lane_node_ids = [str(node.get("id") or "") for node in lane_nodes if str(node.get("id") or "")]

        _append_lane_spine(
            lines=lines,
            left_anchor=left_anchor,
            right_anchor=right_anchor,
            lane_node_ids=lane_node_ids,
        )

        lines.append("  }")

    _append_lane_boundary_subgraphs(lines, left_boundary_nodes, right_boundary_nodes)
    _append_lane_boundary_guides(lines, left_boundary_nodes, right_boundary_nodes)


def _append_swimlane_lane_nodes(
    lines: list[str],
    lane_nodes: list[dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    options: RenderOptions,
) -> None:
    lane_nodes_by_id = _build_nodes_by_id(lane_nodes)
    _append_clustered_node_passes(
        lines=lines,
        ordered_nodes=lane_nodes,
        nodes_by_id=lane_nodes_by_id,
        children_by_parent=children_by_parent,
        options=options,
        indent="    ",
    )


def _append_flowchart_nodes(lines: list[str], nodes: list[dict[str, Any]], options: RenderOptions) -> None:
    nodes_by_id = _build_nodes_by_id(nodes)
    children_by_parent = _subprocess_children_map(nodes, nodes_by_id)
    _append_clustered_node_passes(
        lines=lines,
        ordered_nodes=nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        options=options,
        indent="  ",
    )


def _build_nodes_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        nodes_by_id[node_id] = node
    return nodes_by_id


def _append_clustered_node_passes(
    lines: list[str],
    ordered_nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    options: RenderOptions,
    indent: str,
) -> None:
    rendered: set[str] = set()
    active_stack: set[str] = set()

    _append_clustered_node_pass(
        lines=lines,
        ordered_nodes=ordered_nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        rendered=rendered,
        active_stack=active_stack,
        options=options,
        indent=indent,
        top_level_only=True,
    )
    _append_clustered_node_pass(
        lines=lines,
        ordered_nodes=ordered_nodes,
        nodes_by_id=nodes_by_id,
        children_by_parent=children_by_parent,
        rendered=rendered,
        active_stack=active_stack,
        options=options,
        indent=indent,
        top_level_only=False,
    )


def _append_clustered_node_pass(
    lines: list[str],
    ordered_nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    rendered: set[str],
    active_stack: set[str],
    options: RenderOptions,
    indent: str,
    top_level_only: bool,
) -> None:
    for node in ordered_nodes:
        node_id = str(node.get("id") or "")
        if not node_id or node_id in rendered:
            continue
        if top_level_only and _has_visible_parent(node, nodes_by_id):
            continue
        _append_node_or_subprocess_cluster(
            lines=lines,
            node_id=node_id,
            nodes_by_id=nodes_by_id,
            children_by_parent=children_by_parent,
            rendered=rendered,
            active_stack=active_stack,
            options=options,
            indent=indent,
        )


def _has_visible_parent(node: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> bool:
    parent_id = _subprocess_parent(node)
    return bool(parent_id and parent_id in nodes_by_id)


def _subprocess_children_map(
    nodes: list[dict[str, Any]],
    nodes_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    children_by_parent: dict[str, list[str]] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        parent_id = _subprocess_parent(node)
        if not node_id or not parent_id or parent_id not in nodes_by_id:
            continue
        children_by_parent.setdefault(parent_id, []).append(node_id)
    return children_by_parent


def _append_node_or_subprocess_cluster(
    lines: list[str],
    node_id: str,
    nodes_by_id: dict[str, dict[str, Any]],
    children_by_parent: dict[str, list[str]],
    rendered: set[str],
    active_stack: set[str],
    options: RenderOptions,
    indent: str,
) -> None:
    if node_id in rendered:
        return

    node = nodes_by_id.get(node_id)
    if node is None:
        return

    if node_id in active_stack:
        lines.extend(_render_node_line(node, indent=indent, options=options))
        rendered.add(node_id)
        return

    active_stack.add(node_id)

    child_ids = [child_id for child_id in children_by_parent.get(node_id, []) if child_id in nodes_by_id]
    kind = str(node.get("kind") or node.get("type") or "task").strip().lower()
    has_subprocess_children = kind == "subprocess" and bool(child_ids)

    if has_subprocess_children:
        cluster_id = _safe_cluster_id(f"subprocess_{node_id}")
        cluster_label = str(node.get("name") or node_id)
        lines.append(f"{indent}subgraph cluster_{cluster_id} {{")
        lines.append(f'{indent}  label="{_escape(cluster_label)}";')
        lines.append(f'{indent}  style="rounded,dashed";')
        lines.append(f"{indent}  penwidth=1.6;")
        lines.append(f"{indent}  color=gray55;")
        lines.append(f'{indent}  fillcolor="gray98";')
        lines.append(f"{indent}  labelloc=t;")
        lines.append(f"{indent}  labeljust=l;")
        lines.extend(_render_node_line(node, indent=f"{indent}  ", options=options))
        rendered.add(node_id)
        for child_id in child_ids:
            _append_node_or_subprocess_cluster(
                lines=lines,
                node_id=child_id,
                nodes_by_id=nodes_by_id,
                children_by_parent=children_by_parent,
                rendered=rendered,
                active_stack=active_stack,
                options=options,
                indent=f"{indent}  ",
            )
        lines.append(f"{indent}}}")
    else:
        lines.extend(_render_node_line(node, indent=indent, options=options))
        rendered.add(node_id)
        for child_id in child_ids:
            _append_node_or_subprocess_cluster(
                lines=lines,
                node_id=child_id,
                nodes_by_id=nodes_by_id,
                children_by_parent=children_by_parent,
                rendered=rendered,
                active_stack=active_stack,
                options=options,
                indent=indent,
            )

    active_stack.remove(node_id)


def _subprocess_parent(node: dict[str, Any]) -> str | None:
    value = node.get("subprocess_parent")
    if value is None:
        return None
    parent_id = str(value).strip()
    return parent_id or None


def _append_edges(
    lines: list[str],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
) -> None:
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        edge_attrs = _edge_attrs(
            edge=edge,
            source=str(source),
            target=str(target),
            options=options,
            use_swimlanes=use_swimlanes,
            node_lanes=node_lanes,
        )
        lines.append(
            f'  "{_escape(str(source))}" -> "{_escape(str(target))}" '
            f'[{", ".join(edge_attrs)}];'
        )


def _edge_attrs(
    edge: dict[str, Any],
    source: str,
    target: str,
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
) -> list[str]:
    edge_attrs: list[str] = []
    if use_swimlanes and _is_cross_lane_edge(source, target, node_lanes):
        # Keep lane centerlines stable: cross-lane flow should not re-rank lanes.
        edge_attrs.append("constraint=false")

    if options.detail != "summary":
        branch_label = edge.get("outcome") or edge.get("label")
        if branch_label is not None:
            edge_attrs.append(f'label="{_escape(str(branch_label))}"')

    return edge_attrs


def _extract_nodes_and_edges(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if process is None:
        return [], []

    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_from_ir_object(process)

    if isinstance(process, dict):
        return _extract_from_dict(process)

    return [], []


def _node_lane_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        out[node_id] = str(node.get("lane") or "")
    return out


def _is_cross_lane_edge(source: str, target: str, node_lanes: dict[str, str]) -> bool:
    source_lane = node_lanes.get(source, "")
    target_lane = node_lanes.get(target, "")
    if not source_lane or not target_lane:
        return False
    return source_lane != target_lane


def _extract_from_ir_object(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    for node in getattr(process, "nodes", []) or []:
        attrs = getattr(node, "attrs", {}) or {}
        name = attrs.get("name") if isinstance(attrs, dict) else None
        lane = attrs.get("lane") if isinstance(attrs, dict) else None
        note = attrs.get("note") if isinstance(attrs, dict) else None
        subprocess_parent = attrs.get("subprocess_parent") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": name,
                "lane": lane,
                "note": note,
                "subprocess_parent": subprocess_parent,
            }
        )

    edges = []
    for edge in getattr(process, "edges", []) or []:
        edges.append(
            {
                "source": getattr(edge, "source", None),
                "target": getattr(edge, "target", None),
                "outcome": getattr(edge, "outcome", None),
                "label": getattr(edge, "label", None),
            }
        )
    return nodes, edges


def _extract_from_dict(process: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_raw = process.get("nodes") or []
    edges_raw = process.get("edges") or []
    nodes: list[dict[str, Any]] = []
    for node in nodes_raw:
        if not isinstance(node, dict):
            continue
        node_entry = dict(node)
        attrs = node_entry.get("attrs")
        if "subprocess_parent" not in node_entry and isinstance(attrs, dict):
            parent_id = attrs.get("subprocess_parent")
            if parent_id is not None:
                node_entry["subprocess_parent"] = parent_id
        nodes.append(node_entry)
    edges = [e for e in edges_raw if isinstance(e, dict)]
    return nodes, edges


def _shape_for_kind(kind: str) -> str:
    norm = (kind or "task").lower()
    if norm == "start":
        return "ellipse"
    if norm == "end":
        return "ellipse"
    if norm == "wait":
        return "circle"
    if norm == "decision":
        return "diamond"
    if norm == "subprocess":
        return "component"
    if norm == "queue":
        return "box"
    return "box"


def _node_label(node_id: str, name: str, kind: str, lane: str, note: str, options: RenderOptions) -> str:
    if options.detail == "summary":
        base = name or node_id
        return _with_note(base, note, options)

    if options.detail == "verbose":
        base = name or node_id
        if options.profile == "analysis":
            if lane:
                return _with_note(f"{base}\\n{node_id}\\n[{kind}|lane:{lane}]", note, options)
            return _with_note(f"{base}\\n{node_id}\\n[{kind}]", note, options)
        return _with_note(f"{base}\\n{node_id}", note, options)

    # standard
    return _with_note(name or node_id, note, options)


def _render_node_line(node: dict[str, Any], indent: str, options: RenderOptions) -> list[str]:
    node_id = str(node.get("id", ""))
    if not node_id:
        return []
    kind = str(node.get("kind") or node.get("type") or "task")
    lane = str(node.get("lane") or "")
    note = str(node.get("note") or "")
    label_name = str(node.get("name") or node_id)
    label = _node_label(node_id=node_id, name=label_name, kind=kind, lane=lane, note=note, options=options)
    shape = _shape_for_kind(kind)
    node_attrs = [f'label="{_escape(label)}"', f"shape={shape}"]
    if (kind or "").strip().lower() == "subprocess":
        node_attrs.append('style="rounded,filled"')
        node_attrs.append('fillcolor="lightsteelblue1"')
        node_attrs.append("color=steelblue4")
        node_attrs.append("penwidth=1.4")
    if shape == "diamond":
        # Keep decision diamonds visually balanced instead of overly wide.
        node_attrs.append("regular=true")
    return [f'{indent}"{_escape(node_id)}" [{", ".join(node_attrs)}];']


def _with_note(base: str, note: str, options: RenderOptions) -> str:
    if not options.show_notes:
        return base
    note_text = " ".join((note or "").split())
    if not note_text:
        return base
    return f"{base}\\n\\nNote: {note_text}"


def _partition_nodes_by_lane(nodes: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    lane_groups: dict[str, list[dict[str, Any]]] = {}
    unlaned_nodes: list[dict[str, Any]] = []

    for node in nodes:
        lane = node.get("lane")
        if lane is None or str(lane).strip() == "":
            unlaned_nodes.append(node)
            continue
        lane_key = str(lane)
        lane_groups.setdefault(lane_key, []).append(node)

    return lane_groups, unlaned_nodes


def _lane_fillcolor(index: int) -> str:
    palette = ["gray96", "gray93"]
    return palette[index % len(palette)]


def _append_lane_boundary_subgraphs(lines: list[str], left_nodes: list[str], right_nodes: list[str]) -> None:
    if left_nodes:
        lines.append("  subgraph lane_left_boundary {")
        lines.append("    rank=same;")
        for node in left_nodes:
            lines.append(f'    "{node}";')
        lines.append("  }")

    if right_nodes:
        lines.append("  subgraph lane_right_boundary {")
        lines.append("    rank=same;")
        for node in right_nodes:
            lines.append(f'    "{node}";')
        lines.append("  }")


def _append_lane_boundary_guides(lines: list[str], left_nodes: list[str], right_nodes: list[str]) -> None:
    for boundary_nodes in (left_nodes, right_nodes):
        for source, target in zip(boundary_nodes, boundary_nodes[1:]):
            lines.append(
                f'  "{source}" -> "{target}" [style=invis, weight=200, minlen=1];'
            )


def _append_lane_spine(
    lines: list[str],
    left_anchor: str,
    right_anchor: str,
    lane_node_ids: list[str],
) -> None:
    chain: list[str] = [left_anchor, *[_escape(node_id) for node_id in lane_node_ids], right_anchor]
    if len(chain) < 2:
        return

    for source, target in zip(chain, chain[1:]):
        lines.append(
            f'    "{source}" -> "{target}" [style=invis, weight=200, minlen=2];'
        )


def _safe_cluster_id(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch in {"_", "-"}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    out = "".join(cleaned).strip("_")
    return out or "lane"


def _escape(text: str) -> str:
    return text.replace('"', '\\"')
