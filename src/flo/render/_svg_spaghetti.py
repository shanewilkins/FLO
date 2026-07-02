"""Minimal direct-SVG spaghetti renderer for explicit spatial layouts."""

from __future__ import annotations

import hashlib
from html import escape
from typing import Any

from flo.compiler.analysis import (
    aggregate_material_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
    extract_process_metadata,
    infer_material_movements,
    infer_people_movements,
)

from ._artifact import RenderArtifact
from .options import RenderOptions

_PADDING = 40.0
_SCALE = 80.0
_NODE_WIDTH = 120.0
_NODE_HEIGHT = 48.0


def render_spaghetti_svg_artifact(
    process: dict[str, Any] | Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render a minimal standalone SVG for spaghetti maps with spatial metadata."""
    material_movements = infer_material_movements(process)
    people_movements = infer_people_movements(process)
    material_routes = aggregate_material_movements(material_movements)
    people_routes = _spaghetti_people_routes(people_movements, options)
    locations = extract_location_spatial_index(process)
    include_material, include_people = _spaghetti_channels(options)

    routes_for_locations: list[dict[str, Any]] = []
    if include_material:
        routes_for_locations.extend(material_routes)
    if include_people:
        routes_for_locations.extend(people_routes)

    location_ids = _ordered_location_ids(locations, routes_for_locations)
    if location_ids:
        _ensure_spatial_coordinates(locations=locations, location_ids=location_ids)

    boundary = _extract_spaghetti_boundary(process)
    width, height, project = _projection(locations=locations, boundary=boundary)

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" '
            'data-flo-artifact-kind="svg" data-flo-backend="svg">'
        ),
        '<rect width="100%" height="100%" fill="white" />',
    ]

    if boundary is not None:
        boundary_svg = _boundary_svg(boundary=boundary, project=project)
        if boundary_svg:
            parts.extend(boundary_svg)

    if include_material:
        for route in material_routes:
            parts.extend(
                _route_svg(
                    route=route,
                    options=options,
                    locations=locations,
                    project=project,
                    channel="material",
                )
            )
    if include_people:
        for route in people_routes:
            parts.extend(
                _route_svg(
                    route=route,
                    options=options,
                    locations=locations,
                    project=project,
                    channel="people",
                )
            )

    for location_id in location_ids:
        info = locations.get(location_id, {"name": location_id})
        parts.extend(_location_svg(location_id=location_id, info=info, project=project))

    parts.append("</svg>")
    return RenderArtifact(kind="svg", content="\n".join(parts), backend="svg"), None


def _ensure_spatial_coordinates(
    *, locations: dict[str, dict[str, Any]], location_ids: list[str]
) -> None:
    missing = [
        location_id
        for location_id in location_ids
        if not _has_spatial_coords(locations.get(location_id, {}))
    ]
    if missing:
        joined = ", ".join(sorted(missing))
        raise ValueError(
            "Direct SVG spaghetti rendering requires explicit spatial metadata "
            f"for all rendered locations. Missing: {joined}"
        )


def _has_spatial_coords(info: dict[str, Any]) -> bool:
    return isinstance(info.get("x"), (int, float)) and isinstance(
        info.get("y"), (int, float)
    )


def _projection(
    *, locations: dict[str, dict[str, Any]], boundary: dict[str, Any] | None
) -> tuple[float, float, Any]:
    points: list[tuple[float, float]] = []
    for info in locations.values():
        x = info.get("x")
        y = info.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            points.append((float(x), float(y)))

    if boundary is not None:
        points.extend(boundary.get("points", []))

    if not points:
        min_x = min_y = 0.0
        max_x = max_y = 1.0
    else:
        min_x = min(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_x = max(point[0] for point in points)
        max_y = max(point[1] for point in points)

    span_x = max(1.0, max_x - min_x)
    span_y = max(1.0, max_y - min_y)
    width = (span_x * _SCALE) + (_PADDING * 2)
    height = (span_y * _SCALE) + (_PADDING * 2)

    def _project(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        svg_x = _PADDING + ((x - min_x) * _SCALE)
        svg_y = _PADDING + ((max_y - y) * _SCALE)
        return svg_x, svg_y

    return width, height, _project


def _location_svg(*, location_id: str, info: dict[str, Any], project: Any) -> list[str]:
    x, y = project((float(info.get("x") or 0.0), float(info.get("y") or 0.0)))
    fill, stroke, shape = _location_style(info)
    label = escape(str(info.get("name") or location_id))
    group = [
        f'<g data-location-id="{escape(location_id)}" data-location-shape="{shape}">'
    ]
    if shape == "rect":
        group.append(
            f'<rect x="{x - (_NODE_WIDTH / 2):.1f}" y="{y - (_NODE_HEIGHT / 2):.1f}" '
            f'width="{_NODE_WIDTH:.1f}" height="{_NODE_HEIGHT:.1f}" '
            f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    elif shape == "diamond":
        group.append(
            f'<polygon points="{x:.1f},{y - 28:.1f} {x + 56:.1f},{y:.1f} {x:.1f},{y + 28:.1f} {x - 56:.1f},{y:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    else:
        group.append(
            f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="60" ry="24" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
        )
    group.append(
        f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-family="Helvetica" font-size="14">{label}</text>'
    )
    group.append("</g>")
    return group


def _route_svg(
    *,
    route: dict[str, Any],
    options: RenderOptions,
    locations: dict[str, dict[str, Any]],
    project: Any,
    channel: str,
) -> list[str]:
    source = str(route.get("from_location") or "")
    target = str(route.get("to_location") or "")
    if not source or not target:
        return []
    source_info = locations.get(source, {})
    target_info = locations.get(target, {})

    from_point = project(
        (float(source_info.get("x") or 0.0), float(source_info.get("y") or 0.0))
    )
    to_point = project(
        (float(target_info.get("x") or 0.0), float(target_info.get("y") or 0.0))
    )
    stroke, dash = _route_style(route=route, options=options, channel=channel)
    count = max(1, int(route.get("count") or 0))
    stroke_width = min(6.0, 1.0 + (0.7 * count))
    mid_x = (from_point[0] + to_point[0]) / 2.0
    mid_y = (from_point[1] + to_point[1]) / 2.0
    label = escape(
        _route_label(channel=channel, route=route, count=count, options=options)
    )

    parts = [
        (
            f'<g data-route-channel="{channel}" data-from="{escape(source)}" '
            f'data-to="{escape(target)}">'
        ),
        (
            f'<line x1="{from_point[0]:.1f}" y1="{from_point[1]:.1f}" '
            f'x2="{to_point[0]:.1f}" y2="{to_point[1]:.1f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width:.1f}" '
            f"{dash} />"
        ),
        (
            f'<text x="{mid_x:.1f}" y="{mid_y - 6:.1f}" text-anchor="middle" '
            f'font-family="Helvetica" font-size="12" fill="{stroke}">{label}</text>'
        ),
    ]

    title = _route_title(route=route, channel=channel)
    if title is not None:
        parts.append(f"<title>{escape(title)}</title>")

    parts.append("</g>")
    return parts


def _route_style(
    *, route: dict[str, Any], options: RenderOptions, channel: str
) -> tuple[str, str]:
    if channel != "people":
        return "tomato", 'stroke-linecap="round"'

    if _spaghetti_people_mode(options) == "aggregate":
        return "royalblue", 'stroke-dasharray="8 6" stroke-linecap="round"'

    worker = _spaghetti_primary_worker(route)
    if not worker:
        return "royalblue", 'stroke-dasharray="8 6" stroke-linecap="round"'

    color, dash = _spaghetti_worker_style(worker)
    dash_attr = f'stroke-dasharray="{dash}" ' if dash else ""
    return color, f'{dash_attr}stroke-linecap="round"'


def _route_label(
    *, channel: str, route: dict[str, Any], count: int, options: RenderOptions
) -> str:
    if channel != "people":
        return f"M {count}x"
    worker = _spaghetti_primary_worker(route)
    if _spaghetti_people_mode(options) == "worker" and worker:
        return f"P {worker} {count}x"
    return f"P {count}x"


def _route_title(route: dict[str, Any], channel: str) -> str | None:
    key = "items" if channel == "material" else "workers"
    values = route.get(key) if isinstance(route.get(key), list) else []
    if not values:
        return None
    prefix = "items" if channel == "material" else "workers"
    return prefix + ": " + ", ".join(str(value) for value in values)


def _location_style(info: dict[str, Any]) -> tuple[str, str, str]:
    kind = _canonical_spaghetti_location_kind(info.get("kind"))
    if kind == "storage":
        return "lemonchiffon", "goldenrod", "rect"
    if kind == "transit":
        return "mintcream", "slategray", "diamond"
    if kind == "processing":
        return "mistyrose", "firebrick", "ellipse"
    if kind == "staging":
        return "honeydew", "seagreen", "rect"
    if kind == "support":
        return "azure", "deepskyblue", "rect"
    return "aliceblue", "steelblue", "ellipse"


def _spaghetti_channels(options: RenderOptions) -> tuple[bool, bool]:
    channel = str(options.spaghetti_channel or "both")
    if channel == "material":
        return True, False
    if channel == "people":
        return False, True
    return True, True


def _spaghetti_people_mode(options: RenderOptions) -> str:
    return (
        "worker"
        if str(options.spaghetti_people_mode or "aggregate") == "worker"
        else "aggregate"
    )


def _spaghetti_people_routes(
    people_movements: list[dict[str, Any]], options: RenderOptions
) -> list[dict[str, Any]]:
    if _spaghetti_people_mode(options) == "worker":
        return aggregate_people_movements_by_worker(people_movements)
    return aggregate_people_movements(people_movements)


def _spaghetti_primary_worker(route: dict[str, Any]) -> str | None:
    workers = route.get("workers") if isinstance(route.get("workers"), list) else []
    if not workers:
        return None
    worker = str(workers[0]).strip()
    return worker or None


def _spaghetti_worker_style(worker: str) -> tuple[str, str]:
    palette = [
        ("royalblue", "8 6"),
        ("forestgreen", "4 6"),
        ("darkorange", ""),
        ("firebrick", "10 4"),
        ("purple", "8 6"),
        ("deepskyblue", "4 6"),
        ("sienna", ""),
        ("darkgoldenrod", "10 4"),
    ]
    index = _stable_palette_index(worker, len(palette))
    return palette[index]


def _stable_palette_index(text: str, size: int) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:4], "big", signed=False)
    return seed % max(1, size)


def _ordered_location_ids(
    locations: dict[str, dict[str, Any]], routes: list[dict[str, Any]]
) -> list[str]:
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


_SPAGHETTI_LOCATION_KIND_ALIASES = {
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


def _canonical_spaghetti_location_kind(kind_raw: Any) -> str | None:
    if kind_raw is None:
        return None
    token = str(kind_raw).strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in token:
        token = token.replace("__", "_")
    token = token.strip("_")
    if not token:
        return None
    return _SPAGHETTI_LOCATION_KIND_ALIASES.get(token, token)


def _extract_spaghetti_boundary(process: dict[str, Any] | Any) -> dict[str, Any] | None:
    process_metadata = extract_process_metadata(process)
    boundary_candidate = _extract_boundary_candidate(process_metadata)
    points = _boundary_points(boundary_candidate)
    if len(points) < 3:
        return None
    boundary: dict[str, Any] = {"points": points}
    if isinstance(boundary_candidate, dict):
        boundary["name"] = boundary_candidate.get("name")
        boundary["label"] = boundary_candidate.get("label")
    return boundary


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


def _rectangle_bounds(
    boundary: dict[str, Any],
) -> tuple[float, float, float, float] | None:
    origin_x = _as_number(boundary.get("x"))
    origin_y = _as_number(boundary.get("y"))
    width = _as_number(boundary.get("width"))
    height = _as_number(boundary.get("height"))
    if origin_x is not None and origin_y is not None and width and height:
        if width > 0 and height > 0:
            return origin_x, origin_y, origin_x + width, origin_y + height

    min_x = _as_number(boundary.get("min_x"))
    min_y = _as_number(boundary.get("min_y"))
    max_x = _as_number(boundary.get("max_x"))
    max_y = _as_number(boundary.get("max_y"))
    if None in {min_x, min_y, max_x, max_y}:
        return None
    assert min_x is not None
    assert min_y is not None
    assert max_x is not None
    assert max_y is not None
    if min_x == max_x or min_y == max_y:
        return None
    return min(min_x, max_x), min(min_y, max_y), max(min_x, max_x), max(min_y, max_y)


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _boundary_svg(boundary: dict[str, Any], project: Any) -> list[str]:
    points = boundary.get("points", [])
    if len(points) < 3:
        return []
    svg_points = [project(point) for point in points]
    point_attr = " ".join(f"{x:.1f},{y:.1f}" for x, y in svg_points)
    parts = [
        f'<polygon points="{point_attr}" fill="none" stroke="gray" stroke-width="1.5" stroke-dasharray="6 4" />'
    ]
    label = _boundary_label(boundary)
    if label:
        centroid = _boundary_centroid(points)
        x, y = project(centroid)
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="Helvetica" font-size="11" fill="gray">{escape(label)}</text>'
        )
    return parts


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
