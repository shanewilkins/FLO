"""Queue baseline and direct midpoint SVG postprocessing helpers."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from flo.services._svg_utils import (
    _set_arrow_polygon_horizontal,
    _set_edge_path,
    _svg_edge_groups,
    _svg_node_outer_bounds,
    _write_svg_tree,
)


def _postprocess_direct_midpoint_edges_svg(*, output_path: Path) -> None:
    """Rewrite direct e/w edges to exact side-midpoint connectors."""
    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    node_groups = _svg_node_groups(root)
    edge_groups = _svg_edge_groups(root)

    updated = False
    for title, group in edge_groups.items():
        match = re.match(
            r"^(?P<source>[^:]+):(?P<source_side>[nsew])->(?P<target>[^:]+):(?P<target_side>[nsew])$",
            title,
        )
        if match is None:
            continue

        source_id = match.group("source")
        target_id = match.group("target")
        source_side = match.group("source_side")
        target_side = match.group("target_side")
        if source_side not in {"e", "w"} or target_side not in {"e", "w"}:
            continue
        if source_id.startswith("__") or target_id.startswith("__"):
            continue

        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        if source_bounds is None or target_bounds is None:
            continue

        source_x, source_y, target_x, target_y = _apply_triangle_attachment(
            node_groups,
            source_id,
            target_id,
            source_side,
            target_side,
            source_bounds,
            target_bounds,
        )

        # Skip edges that are already correct to avoid introducing Y drift.
        if _should_skip_edge_rewrite(group, source_y, target_y):
            continue

        _set_edge_path(group, [(source_x, source_y), (target_x, target_y)])
        _set_arrow_polygon_horizontal(
            group,
            tip=(target_x, target_y),
            direction=(1 if target_x >= source_x else -1),
        )
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _postprocess_queue_baseline_alignment_svg(*, output_path: Path) -> None:
    """Shift queue triangles so side-midpoint attachments sit on mainline baseline."""
    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    node_groups = _svg_node_groups(root)
    edge_groups = _svg_edge_groups(root)

    updated = False
    for node_id, group in node_groups.items():
        triangle = _node_queue_triangle_vertices(group)
        if triangle is None:
            continue

        baseline_ys = _queue_baseline_candidates(
            queue_id=node_id,
            node_groups=node_groups,
            node_bounds=node_bounds,
            edge_groups=edge_groups,
        )
        if not baseline_ys:
            continue

        current_y = _triangle_side_midpoint_y(triangle)
        target_y = sum(baseline_ys) / len(baseline_ys)
        dy = target_y - current_y
        if abs(dy) <= 0.01:
            continue

        _shift_node_group(group, dx=0.0, dy=dy)
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _should_skip_edge_rewrite(
    group: ET.Element,
    source_y: float,
    target_y: float,
) -> bool:
    """Check if edge should be skipped (already horizontal at correct Y)."""
    start_point, end_point = _edge_path_start_end(group)
    if start_point is None or end_point is None:
        return False
    return (
        abs(start_point[1] - end_point[1]) <= 0.01
        and abs(start_point[1] - source_y) <= 0.01
        and abs(end_point[1] - target_y) <= 0.01
    )


def _apply_triangle_attachment(
    node_groups: dict[str, ET.Element],
    source_id: str,
    target_id: str,
    source_side: str,
    target_side: str,
    source_bounds: tuple[float, float, float, float],
    target_bounds: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    source_triangle_point = _triangle_side_midpoint(
        group=node_groups.get(source_id),
        side=source_side,
    )
    target_triangle_point = _triangle_side_midpoint(
        group=node_groups.get(target_id),
        side=target_side,
    )

    source_x = source_bounds[2] if source_side == "e" else source_bounds[0]
    source_y = (source_bounds[1] + source_bounds[3]) / 2.0
    target_x = target_bounds[0] if target_side == "w" else target_bounds[2]
    target_y = (target_bounds[1] + target_bounds[3]) / 2.0

    if source_triangle_point is not None:
        source_x, source_y = source_triangle_point
    if target_triangle_point is not None:
        target_x, target_y = target_triangle_point

    if source_triangle_point is not None or target_triangle_point is not None:
        source_y, target_y = _apply_triangle_alignment(
            source_triangle_point,
            target_triangle_point,
            source_y,
            target_y,
        )

    return source_x, source_y, target_x, target_y


def _apply_triangle_alignment(
    source_triangle_point: tuple[float, float] | None,
    target_triangle_point: tuple[float, float] | None,
    source_y: float,
    target_y: float,
) -> tuple[float, float]:
    if source_triangle_point is None and target_triangle_point is None:
        return source_y, target_y

    if source_triangle_point is not None and target_triangle_point is not None:
        line_y = (source_y + target_y) / 2.0
    elif source_triangle_point is not None:
        line_y = source_y
    else:
        line_y = target_y

    if source_triangle_point is None:
        source_y = line_y
    if target_triangle_point is None:
        target_y = line_y

    return source_y, target_y


def _queue_baseline_candidates(
    *,
    queue_id: str,
    node_groups: dict[str, ET.Element],
    node_bounds: dict[str, tuple[float, float, float, float]],
    edge_groups: dict[str, ET.Element],
) -> list[float]:
    ys: list[float] = []
    for title in edge_groups:
        if "->" not in title:
            continue
        left, right = title.split("->", 1)

        if _endpoint_matches_node_id(right, queue_id) and _endpoint_compass_side(right) == "w":
            other_id = left.split(":", 1)[0]
            other_y = _adjacent_baseline_y(
                other_id=other_id,
                endpoint=left,
                node_groups=node_groups,
                node_bounds=node_bounds,
            )
            if other_y is not None:
                ys.append(other_y)

        if _endpoint_matches_node_id(left, queue_id) and _endpoint_compass_side(left) == "e":
            other_id = right.split(":", 1)[0]
            other_y = _adjacent_baseline_y(
                other_id=other_id,
                endpoint=right,
                node_groups=node_groups,
                node_bounds=node_bounds,
            )
            if other_y is not None:
                ys.append(other_y)
    return ys


def _adjacent_baseline_y(
    *,
    other_id: str,
    endpoint: str,
    node_groups: dict[str, ET.Element],
    node_bounds: dict[str, tuple[float, float, float, float]],
) -> float | None:
    if other_id.startswith("__"):
        return None
    other_group = node_groups.get(other_id)
    if other_group is None:
        return None
    if _node_queue_triangle_vertices(other_group) is not None:
        return None
    bounds = node_bounds.get(other_id)
    if bounds is None:
        return None

    side = _endpoint_compass_side(endpoint)
    side = side if side in {"e", "w"} else "e"
    _, y = _point_on_bounds(bounds, side)
    return y


def _triangle_side_midpoint_y(
    triangle: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> float:
    apex, base_left, base_right = triangle
    left_mid_y = (apex[1] + base_left[1]) / 2.0
    right_mid_y = (apex[1] + base_right[1]) / 2.0
    return (left_mid_y + right_mid_y) / 2.0


def _shift_node_group(group: ET.Element, *, dx: float, dy: float) -> None:
    for polygon in group.findall("{*}polygon"):
        shifted: list[str] = []
        for token in polygon.attrib.get("points", "").split():
            if "," not in token:
                shifted.append(token)
                continue
            x_text, y_text = token.split(",", 1)
            shifted.append(f"{float(x_text) + dx:.2f},{float(y_text) + dy:.2f}")
        polygon.attrib["points"] = " ".join(shifted)

    for text in group.findall("{*}text"):
        x = text.attrib.get("x")
        y = text.attrib.get("y")
        if x is not None:
            text.attrib["x"] = f"{float(x) + dx:.2f}"
        if y is not None:
            text.attrib["y"] = f"{float(y) + dy:.2f}"


def _svg_node_groups(root: ET.Element) -> dict[str, ET.Element]:
    groups: dict[str, ET.Element] = {}
    for group in root.iter():
        if group.attrib.get("class") != "node":
            continue
        title = group.find("{*}title")
        if title is None or title.text is None:
            continue
        groups[title.text] = group
    return groups


def _triangle_side_midpoint(*, group: ET.Element | None, side: str) -> tuple[float, float] | None:
    if group is None or side not in {"e", "w"}:
        return None

    triangle = _node_queue_triangle_vertices(group)
    if triangle is None:
        return None
    apex, base_left, base_right = triangle
    if side == "w":
        return ((apex[0] + base_left[0]) / 2.0, (apex[1] + base_left[1]) / 2.0)
    return ((apex[0] + base_right[0]) / 2.0, (apex[1] + base_right[1]) / 2.0)


def _node_queue_triangle_vertices(group: ET.Element) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None:
    points: list[tuple[float, float]] = []
    for polygon in group.findall("{*}polygon"):
        fill = (polygon.attrib.get("fill", "") or "").strip().lower()
        stroke = polygon.attrib.get("stroke", "")
        stroke_l = (stroke or "").strip().lower()
        # Support both legacy filled queue triangles and outline-only triangles.
        if stroke_l != "#e65100":
            continue
        if fill not in {"#ff9800", "none", ""}:
            continue
        if not stroke or stroke == "none":
            continue
        points = _polygon_points(polygon.attrib.get("points", ""))
        if points:
            break
    if not points:
        return None

    unique = _unique_polygon_vertices(points)
    if len(unique) != 3:
        return None

    edges = [
        (0, 1, (unique[0][1] + unique[1][1]) / 2.0),
        (1, 2, (unique[1][1] + unique[2][1]) / 2.0),
        (2, 0, (unique[2][1] + unique[0][1]) / 2.0),
    ]
    base_i, base_j, _ = max(edges, key=lambda item: item[2])
    base_a = unique[base_i]
    base_b = unique[base_j]
    apex = next(point for idx, point in enumerate(unique) if idx not in {base_i, base_j})

    if base_a[0] <= base_b[0]:
        base_left, base_right = base_a, base_b
    else:
        base_left, base_right = base_b, base_a
    return apex, base_left, base_right


def _polygon_points(points_text: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for token in points_text.split():
        if "," not in token:
            continue
        x_text, y_text = token.split(",", 1)
        points.append((float(x_text), float(y_text)))
    return points


def _unique_polygon_vertices(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique: list[tuple[float, float]] = []
    for point in points:
        if not unique or point != unique[-1]:
            unique.append(point)
    if len(unique) > 1 and unique[0] == unique[-1]:
        unique.pop()
    return unique


def _endpoint_matches_node_id(endpoint: str, node_id: str) -> bool:
    return endpoint == node_id or endpoint.startswith(f"{node_id}:")


def _endpoint_compass_side(endpoint: str) -> str:
    if ":" not in endpoint:
        return "e"
    side = endpoint.rsplit(":", 1)[-1]
    if side in {"n", "s", "e", "w"}:
        return side
    return "e"


def _point_on_bounds(bounds: tuple[float, float, float, float], side: str) -> tuple[float, float]:
    left, top, right, bottom = bounds
    if side == "n":
        return ((left + right) / 2.0, top)
    if side == "s":
        return ((left + right) / 2.0, bottom)
    if side == "w":
        return (left, (top + bottom) / 2.0)
    if side == "e":
        return (right, (top + bottom) / 2.0)
    return ((left + right) / 2.0, (top + bottom) / 2.0)


def _edge_path_start_end(group: ET.Element) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    path = group.find("{*}path")
    if path is None:
        return None, None
    d = path.attrib.get("d", "")
    coords = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", d)]
    points = [(coords[idx], coords[idx + 1]) for idx in range(0, len(coords) - 1, 2)]
    if not points:
        return None, None
    return points[0], points[-1]
