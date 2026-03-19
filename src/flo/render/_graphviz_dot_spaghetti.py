"""Spaghetti-map DOT helpers for FLO."""

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
    node_attrs.extend(_spaghetti_location_visual_attrs(info))
    x = info.get("x")
    y = info.get("y")
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        node_attrs.append(f'pos="{float(x):.3f},{float(y):.3f}!"')
        node_attrs.append("pin=true")
    return node_attrs


_SPAGHETTI_LOCATION_STYLE_BY_KIND: dict[str, dict[str, str]] = {
    "storage": {"shape": "box", "fillcolor": "lemonchiffon", "color": "goldenrod4"},
    "operation": {"shape": "ellipse", "fillcolor": "aliceblue", "color": "steelblue4"},
    "processing": {"shape": "hexagon", "fillcolor": "mistyrose", "color": "firebrick3"},
    "staging": {"shape": "trapezium", "fillcolor": "honeydew", "color": "seagreen4"},
    "support": {"shape": "octagon", "fillcolor": "azure", "color": "deepskyblue4"},
    "transit": {"shape": "diamond", "fillcolor": "mintcream", "color": "slategray4"},
}


_SPAGHETTI_LOCATION_KIND_ALIASES: dict[str, str] = {
    "storage": "storage",
    "inventory": "storage",
    "warehouse": "storage",
    "stock": "storage",
    "stockroom": "storage",
    "storeroom": "storage",
    "operation": "operation",
    "ops": "operation",
    "work": "operation",
    "workcell": "operation",
    "work_cell": "operation",
    "workstation": "operation",
    "station": "operation",
    "procedure": "operation",
    "prep": "operation",
    "processing": "processing",
    "process": "processing",
    "transform": "processing",
    "transformation": "processing",
    "machine": "processing",
    "machining": "processing",
    "heat": "processing",
    "staging": "staging",
    "buffer": "staging",
    "queue": "staging",
    "holding": "staging",
    "holding_area": "staging",
    "wait": "staging",
    "waiting": "staging",
    "cooling": "staging",
    "support": "support",
    "service": "support",
    "inspection": "support",
    "quality": "support",
    "qa": "support",
    "clean": "support",
    "cleaning": "support",
    "sanitize": "support",
    "sanitization": "support",
    "sterile": "support",
    "sterilization": "support",
    "wash": "support",
    "transit": "transit",
    "corridor": "transit",
    "path": "transit",
    "conveyor": "transit",
    "transfer": "transit",
}


def _spaghetti_location_visual_attrs(info: dict[str, Any]) -> list[str]:
    kind = _canonical_spaghetti_location_kind(info.get("kind"))
    if kind is None:
        return []

    style = _SPAGHETTI_LOCATION_STYLE_BY_KIND.get(kind)
    if style is None:
        return []

    return [
        f"shape={style['shape']}",
        f"fillcolor={style['fillcolor']}",
        f"color={style['color']}",
    ]


def _canonical_spaghetti_location_kind(kind_raw: Any) -> str | None:
    if kind_raw is None:
        return None

    kind = _normalize_location_kind_token(str(kind_raw))
    if not kind:
        return None

    return _SPAGHETTI_LOCATION_KIND_ALIASES.get(kind, kind)


def _normalize_location_kind_token(value: str) -> str:
    token = value.strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in token:
        token = token.replace("__", "_")
    return token.strip("_")


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


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


