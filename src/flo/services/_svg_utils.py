"""Pure SVG geometry helpers for the FLO Graphviz service.

These functions operate on ET.Element trees, coordinate lists, and SVG text.
They have no dependency on domain-specific FLO concepts.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

_SVG_NS = "http://www.w3.org/2000/svg"


def _svg_node_outer_bounds(root: ET.Element) -> dict[str, tuple[float, float, float, float]]:
    """Return bounds from visible outer node borders when available."""
    bounds: dict[str, tuple[float, float, float, float]] = {}
    for group in root.iter():
        if group.attrib.get("class") != "node":
            continue
        title = group.find("{*}title")
        if title is None or title.text is None:
            continue

        points = _svg_group_points(group, border_only=True)
        if not points:
            # Fallback to full node geometry when explicit border points are absent.
            points = _svg_group_points(group, border_only=False)
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        bounds[title.text] = (min(xs), min(ys), max(xs), max(ys))
    return bounds


def _svg_group_points(group: ET.Element, *, border_only: bool) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    points.extend(_svg_polygon_points(group, border_only=border_only))
    points.extend(_svg_path_points(group, border_only=border_only))
    return points


def _svg_polygon_points(group: ET.Element, *, border_only: bool) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for polygon in group.findall("{*}polygon"):
        if border_only:
            stroke = polygon.attrib.get("stroke", "")
            if not stroke or stroke == "none":
                continue
        points.extend(_parse_svg_points(polygon.attrib.get("points", "")))
    return points


def _svg_path_points(group: ET.Element, *, border_only: bool) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for path in group.findall("{*}path"):
        if border_only:
            stroke = path.attrib.get("stroke", "")
            if not stroke or stroke == "none":
                continue
        points.extend(_parse_svg_path_points(path.attrib.get("d", "")))
    return points


def _svg_node_bounds(root: ET.Element) -> dict[str, tuple[float, float, float, float]]:
    bounds: dict[str, tuple[float, float, float, float]] = {}
    for group in root.iter():
        if group.attrib.get("class") != "node":
            continue
        title = group.find("{*}title")
        if title is None or title.text is None:
            continue
        points: list[tuple[float, float]] = []
        for polygon in group.findall("{*}polygon"):
            points.extend(_parse_svg_points(polygon.attrib.get("points", "")))
        for path in group.findall("{*}path"):
            points.extend(_parse_svg_path_points(path.attrib.get("d", "")))
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        bounds[title.text] = (min(xs), min(ys), max(xs), max(ys))
    return bounds


def _svg_edge_groups(root: ET.Element) -> dict[str, ET.Element]:
    groups: dict[str, ET.Element] = {}
    for group in root.iter():
        if group.attrib.get("class") != "edge":
            continue
        title = group.find("{*}title")
        if title is None or title.text is None:
            continue
        groups[title.text] = group
    return groups


def _svg_content_points(root: ET.Element) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for group in root.iter():
        if group.attrib.get("class") not in {"node", "edge"}:
            continue
        for polygon in group.findall("{*}polygon"):
            points.extend(_parse_svg_points(polygon.attrib.get("points", "")))
        for path in group.findall("{*}path"):
            points.extend(_parse_svg_path_points(path.attrib.get("d", "")))
    return points


def _set_svg_background_rect(root: ET.Element, *, x: float, y: float, width: float, height: float) -> None:
    bg_tag = f"{{{_SVG_NS}}}rect"
    parent = root

    # Remove any stale background we may have injected earlier.
    for child in list(parent):
        if child.tag == bg_tag and child.attrib.get("id") == "__flo_canvas_bg":
            parent.remove(child)

    bg = ET.Element(
        bg_tag,
        {
            "id": "__flo_canvas_bg",
            "x": f"{x:.2f}",
            "y": f"{y:.2f}",
            "width": f"{width:.2f}",
            "height": f"{height:.2f}",
            "fill": "#ffffff",
            "fill-opacity": "1",
            "stroke": "none",
        },
    )
    parent.insert(0, bg)


def _ensure_svg_white_background(root: ET.Element) -> None:
    style = root.attrib.get("style", "")
    declarations = [part.strip() for part in style.split(";") if part.strip()]

    filtered = [
        decl
        for decl in declarations
        if not decl.lower().startswith("background:")
        and not decl.lower().startswith("background-color:")
    ]
    filtered.append("background:#ffffff")
    root.attrib["style"] = "; ".join(filtered) + ";"


def _svg_graph_translation(root: ET.Element) -> tuple[float, float]:
    for group in root.iter():
        if group.attrib.get("class") != "graph":
            continue
        transform = group.attrib.get("transform")
        if not transform:
            return (0.0, 0.0)
        return _parse_svg_translate(transform)
    return (0.0, 0.0)


def _parse_svg_translate(transform: str) -> tuple[float, float]:
    rotate_match = re.search(r"rotate\(\s*(-?\d+(?:\.\d+)?)", transform)
    if rotate_match and not math.isclose(float(rotate_match.group(1)), 0.0, abs_tol=1e-9):
        return (0.0, 0.0)

    match = re.search(
        r"translate\(\s*(-?\d+(?:\.\d+)?)\s*(?:[,\s]\s*(-?\d+(?:\.\d+)?))?\s*\)",
        transform,
    )
    if match is None:
        return (0.0, 0.0)
    tx = float(match.group(1))
    ty = float(match.group(2)) if match.group(2) is not None else 0.0
    return (tx, ty)


def _format_svg_length(existing: str, value: float) -> str:
    match = re.match(r"^\s*-?\d+(?:\.\d+)?\s*(?P<unit>[a-zA-Z%]*)\s*$", existing)
    unit = match.group("unit") if match else ""
    return f"{value:.2f}{unit}"


def _set_edge_path(group: ET.Element, points: list[tuple[float, float]]) -> None:
    path = group.find("{*}path")
    if path is None:
        return
    path.attrib["d"] = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def _set_arrow_polygon(group: ET.Element, *, tip: tuple[float, float], direction: int = -1) -> None:
    """Set a vertical arrowhead polygon on an edge group.

    ``direction`` controls which side of the tip the base is placed on:
    - ``-1`` (default): base at ``tip_y - 8`` — arrow points toward increasing Y
      (visually downward in screen space when Graphviz Y-flip is in effect, this
      actually appears as pointing upward; use for edges entering a node from above
      in internal coords).
    - ``+1``: base at ``tip_y + 8`` — flipped; use for return-loop edges that
      approach a node from below in screen space (increasing internal Y direction).
    """
    polygon = group.find("{*}polygon")
    if polygon is None:
        return
    tip_x, tip_y = tip
    offset = 8.0 * direction
    polygon.attrib["points"] = (
        f"{tip_x:.2f},{tip_y:.2f} {tip_x - 4.0:.2f},{tip_y + offset:.2f} {tip_x + 4.0:.2f},{tip_y + offset:.2f} {tip_x:.2f},{tip_y:.2f}"
    )


def _set_arrow_polygon_horizontal(group: ET.Element, *, tip: tuple[float, float], direction: int) -> None:
    polygon = group.find("{*}polygon")
    if polygon is None:
        return
    tip_x, tip_y = tip
    offset = 10.0 * (-1 if direction >= 0 else 1)
    polygon.attrib["points"] = (
        f"{tip_x:.2f},{tip_y:.2f} {tip_x + offset:.2f},{tip_y + 3.5:.2f} {tip_x + offset:.2f},{tip_y - 3.5:.2f} {tip_x:.2f},{tip_y:.2f}"
    )


def _parse_svg_points(points_text: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for token in points_text.split():
        if "," not in token:
            continue
        x_text, y_text = token.split(",", 1)
        points.append((float(x_text), float(y_text)))
    return points


def _parse_svg_path_points(path_text: str) -> list[tuple[float, float]]:
    values = [float(value) for value in re.findall(r'-?\d+(?:\.\d+)?', path_text)]
    return [(values[idx], values[idx + 1]) for idx in range(0, len(values) - 1, 2)]


def _write_svg_tree(tree: ET.ElementTree[ET.Element], output_path: Path) -> None:
    """Write SVG while preserving an unprefixed default SVG namespace."""
    ET.register_namespace("", _SVG_NS)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

