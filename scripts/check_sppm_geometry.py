"""Check final SPPM SVG geometry independently of the layout model."""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from itertools import combinations, pairwise
from pathlib import Path

Box = tuple[float, float, float, float]
Point = tuple[float, float]
NS = {"s": "http://www.w3.org/2000/svg"}
TOLERANCE = 0.6


def shape_bounds(shape: ET.Element) -> Box:
    """Read bounds from renderer-owned rectangular, polygon, or ellipse shapes."""
    if shape.tag.endswith("polygon"):
        points = _points(shape.get("points", ""))
        xs, ys = zip(*points, strict=True)
        return min(xs), min(ys), max(xs), max(ys)
    if shape.tag.endswith("ellipse"):
        cx, cy, rx, ry = (
            float(shape.get(key, "0")) for key in ("cx", "cy", "rx", "ry")
        )
        return cx - rx, cy - ry, cx + rx, cy + ry
    x, y, w, h = (float(shape.get(key, "0")) for key in ("x", "y", "width", "height"))
    return x, y, x + w, y + h


def _points(raw: str) -> tuple[Point, ...]:
    values = [float(value) for value in re.split(r"[\s,]+", raw.strip()) if value]
    return tuple(zip(values[::2], values[1::2], strict=True))


def _overlap(a: Box, b: Box) -> bool:
    return (
        min(a[2], b[2]) > max(a[0], b[0]) + TOLERANCE
        and min(a[3], b[3]) > max(a[1], b[1]) + TOLERANCE
    )


def _shape_overlaps_box(shape: ET.Element, box: Box) -> bool:
    if not _overlap(shape_bounds(shape), box):
        return False
    if not shape.tag.endswith("polygon"):
        return True
    vertices = _points(shape.get("points", ""))
    corners = ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]))
    axes = [(1, 0), (0, 1)] + [
        (b[1] - a[1], a[0] - b[0]) for a, b in pairwise((*vertices, vertices[0]))
    ]
    for x, y in axes:
        length = math.hypot(x, y)
        polygon = [(px * x + py * y) / length for px, py in vertices]
        rectangle = [(px * x + py * y) / length for px, py in corners]
        if (
            min(max(polygon), max(rectangle))
            <= max(min(polygon), min(rectangle)) + TOLERANCE
        ):
            return False
    return True


def _inside(inner: Box, outer: Box) -> bool:
    return (
        inner[0] >= outer[0] - TOLERANCE
        and inner[1] >= outer[1] - TOLERANCE
        and inner[2] <= outer[2] + TOLERANCE
        and inner[3] <= outer[3] + TOLERANCE
    )


def _segment_crosses(a: Point, b: Point, box: Box) -> bool:
    if abs(a[0] - b[0]) < TOLERANCE:
        return (
            box[0] + TOLERANCE < a[0] < box[2] - TOLERANCE
            and min(a[1], b[1]) < box[3] - TOLERANCE
            and max(a[1], b[1]) > box[1] + TOLERANCE
        )
    return (
        box[1] + TOLERANCE < a[1] < box[3] - TOLERANCE
        and min(a[0], b[0]) < box[2] - TOLERANCE
        and max(a[0], b[0]) > box[0] + TOLERANCE
    )


def _on_shape(point: Point, shape: ET.Element) -> bool:
    left, top, right, bottom = shape_bounds(shape)
    if shape.tag.endswith("ellipse"):
        rx, ry = (right - left) / 2, (bottom - top) / 2
        distance = math.hypot((point[0] - left - rx) / rx, (point[1] - top - ry) / ry)
        return abs(distance - 1) * min(rx, ry) <= TOLERANCE
    if shape.tag.endswith("polygon"):
        vertices = _points(shape.get("points", ""))
    else:
        vertices = ((left, top), (right, top), (right, bottom), (left, bottom))
    return any(
        _distance(point, a, b) <= TOLERANCE
        for a, b in pairwise((*vertices, vertices[0]))
    )


def _distance(point: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    ratio = (
        0
        if denominator == 0
        else max(
            0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denominator)
        )
    )
    return math.dist(point, (a[0] + ratio * dx, a[1] + ratio * dy))


def geometry_violations(
    content: str, lane_members: dict[str, list[str]] | None = None
) -> tuple[str, ...]:
    """Find collisions, clipped shapes, diagonal segments, and detached endpoints."""
    root = ET.fromstring(content)
    nodes = {
        node.get("data-node-id"): node[0]
        for node in root.findall(".//s:g[@data-node-id]", NS)
    }
    boxes = {name: shape_bounds(shape) for name, shape in nodes.items()}
    content_group = root.find("s:g[@transform]", NS)
    shift = (
        _points(
            content_group.get("transform", "")
            .removeprefix("translate(")
            .removesuffix(")")
        )[0]
        if content_group is not None
        else (0, 0)
    )
    vx, vy, width, height = map(float, root.get("viewBox", "0 0 0 0").split())
    canvas = vx - shift[0], vy - shift[1], vx + width - shift[0], vy + height - shift[1]
    issues = []
    for name, box in boxes.items():
        if not _inside(box, canvas):
            issues.append(f"node {name} outside canvas")
    frames = {
        lane.get("data-lane-id"): shape_bounds(lane[0])
        for lane in root.findall(".//s:g[@data-lane-id]", NS)
    }
    for lane_id, members in (lane_members or {}).items():
        if lane_id.startswith("__sppm"):
            continue
        if lane_id not in frames:
            issues.append(f"missing lane frame {lane_id}")
            continue
        for node in members:
            if node not in boxes or not _inside(boxes[node], frames[lane_id]):
                issues.append(f"node {node} outside lane {lane_id}")
    for (first, a), (second, b) in combinations(boxes.items(), 2):
        if _overlap(a, b):
            issues.append(f"nodes {first}/{second} overlap")
    annotations = []
    for edge in root.findall(".//s:g[@data-edge-source]", NS):
        source, target = edge.get("data-edge-source"), edge.get("data-edge-target")
        edge_id = f"{source}->{target}"
        line = edge.find("s:polyline", NS)
        points = _points(line.get("points", "")) if line is not None else ()
        if len(points) < 2:
            issues.append(f"edge {edge_id} has no route")
            continue
        for endpoint, node in ((points[0], source), (points[-1], target)):
            if node not in nodes or not _on_shape(endpoint, nodes[node]):
                issues.append(f"edge {edge_id} detached at {node}")
        for a, b in pairwise(points):
            if abs(a[0] - b[0]) > TOLERANCE and abs(a[1] - b[1]) > TOLERANCE:
                issues.append(f"edge {edge_id} is diagonal")
            for name, box in boxes.items():
                if name not in (source, target) and _segment_crosses(a, b, box):
                    issues.append(f"edge {edge_id} crosses node {name}")
            if not _inside(
                (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])),
                canvas,
            ):
                issues.append(f"edge {edge_id} outside canvas")
        for rect in edge.findall(".//s:rect", NS):
            box = shape_bounds(rect)
            annotations.append((edge_id, box))
            if not _inside(box, canvas):
                issues.append(f"annotation {edge_id} outside canvas")
            for name in boxes:
                if _shape_overlaps_box(nodes[name], box):
                    issues.append(f"annotation {edge_id} overlaps node {name}")
    for (first, a), (second, b) in combinations(annotations, 2):
        if _overlap(a, b):
            issues.append(f"annotations {first}/{second} overlap")
    return tuple(sorted(set(issues)))


def main() -> int:
    """Verify selected SVGs, defaulting to the committed release corpus."""
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted(
        (Path(__file__).resolve().parents[1] / "tests/golden/sppm").glob("*/render.svg")
    )
    failures = []
    for path in paths:
        layout_file = path.with_name("layout_result.json")
        lanes = (
            json.loads(layout_file.read_text()).get("lanes", [])
            if layout_file.is_file()
            else []
        )
        members = {lane["id"]: lane["node_ids"] for lane in lanes}
        failures.extend(
            f"{path}: {issue}"
            for issue in geometry_violations(path.read_text(), members)
        )
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"Checked {len(paths)} SVGs; {len(failures)} final geometry violation(s).")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
