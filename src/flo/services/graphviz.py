"""Graphviz rendering service for FLO.

Provides a thin wrapper around the system `dot` binary that converts DOT
source into an image file.  The DOT pipeline is kept as a separate step so
that FLO's core rendering logic never depends on Graphviz being installed.
"""

from __future__ import annotations

import math
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from flo.services.errors import RenderError

_SUPPORTED_FORMATS = {"png", "svg", "pdf", "eps", "ps"}
_SVG_OUTER_PADDING_PX = 6.0
_SVG_NS = "http://www.w3.org/2000/svg"


def render_dot_to_file(dot: str, output_path: str) -> None:
    """Render DOT source to an image file via the system `dot` binary.

    The output format is inferred from the file extension.  Supported
    extensions: ``.png``, ``.svg``, ``.pdf``, ``.eps``, ``.ps``.

    Raises :class:`~flo.services.errors.RenderError` with exit code ``5``
    if ``dot`` is not found on PATH or the subprocess fails.
    """
    if not shutil.which("dot"):
        raise RenderError(
            "Graphviz 'dot' not found on PATH. "
            "Install Graphviz (https://graphviz.org/download/) or pipe DOT "
            "output manually: flo run model.flo | dot -Tpng -o output.png"
        )

    fmt = Path(output_path).suffix.lstrip(".").lower()
    if fmt not in _SUPPORTED_FORMATS:
        raise RenderError(
            f"Unsupported output format '.{fmt}'. "
            f"Supported extensions: {', '.join(sorted(_SUPPORTED_FORMATS))}"
        )

    try:
        result = subprocess.run(
            ["dot", f"-T{fmt}", "-o", output_path],
            input=dot,
            text=True,
            capture_output=True,
        )
    except OSError as e:
        raise RenderError(f"Failed to invoke Graphviz 'dot': {e}")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RenderError(
            f"Graphviz 'dot' exited with code {result.returncode}"
            + (f": {stderr}" if stderr else "")
        )

    # SVG gets a small FLO-owned postprocess layer:
    # 1) normalize wrapped SPPM boundary doglegs where Graphviz can drift;
    # 2) normalize outer SVG padding so borders are small and even.
    # Future work: extend similar canvas normalization to non-SVG formats.
    if fmt == "svg":
        svg_path = Path(output_path)
        if not svg_path.exists():
            return
        _postprocess_wrapped_sppm_svg(dot=dot, output_path=svg_path)
        _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
        _normalize_node_backing_fills_svg(output_path=svg_path)
        _normalize_svg_outer_padding(output_path=svg_path, padding=_SVG_OUTER_PADDING_PX)


def _postprocess_wrapped_sppm_svg(*, dot: str, output_path: Path) -> None:
    # Rewrite wrapped SPPM boundary edges into deterministic doglegs.
    #
    # Why this exists:
    # - Graphviz can route wrapped boundary edges through visually incorrect
    #   approaches even when DOT ports/hints are deterministic.
    # - Product requirement is a strict path shape: right, down, left,
    #   then centered vertical drop into the target.
    #
    # Scope is intentionally narrow:
    # - only wrapped LR SPPM boundary transitions via __wrap_exit_lr_*;
    # - only SVG output (node bounds available from rendered geometry);
    # - no changes to non-SPPM or non-boundary edges.
    boundary_pairs = _wrapped_sppm_boundary_pairs(dot)
    if not boundary_pairs:
        return

    tree = ET.parse(output_path)
    root = tree.getroot()

    node_bounds = _svg_node_bounds(root)
    edge_groups = _svg_edge_groups(root)
    updated = False

    for anchor_id, (source_id, target_id) in boundary_pairs.items():
        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        first_group = edge_groups.get(f"{source_id}:e->{anchor_id}")
        second_group = edge_groups.get(f"{anchor_id}->{target_id}:s")
        if second_group is None:
            second_group = edge_groups.get(f"{anchor_id}->{target_id}:n")
        if source_bounds is None or target_bounds is None or first_group is None or second_group is None:
            continue

        # Route policy: leave the source from the right edge at its vertical
        # midpoint, run through a right-side corridor, approach above target,
        # then drop vertically into target top-center.
        source_right = source_bounds[2]
        source_mid_y = (source_bounds[1] + source_bounds[3]) / 2.0
        target_center_x = (target_bounds[0] + target_bounds[2]) / 2.0
        target_top_y = target_bounds[1]
        approach_y = target_top_y - 12.0
        # Keep the dogleg corridor outside the source box without pinning it
        # against the far-right graph edge, which creates uneven margins.
        corridor_x = source_right + 12.0

        _set_edge_path(
            first_group,
            [
                (source_right, source_mid_y),
                (corridor_x, source_mid_y),
                (corridor_x, approach_y),
                (target_center_x, approach_y),
            ],
        )
        _set_edge_path(
            second_group,
            [
                (target_center_x, approach_y),
                (target_center_x, target_top_y),
            ],
        )
        _set_arrow_polygon(second_group, tip=(target_center_x, target_top_y))
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _normalize_svg_outer_padding(*, output_path: Path, padding: float) -> None:
    """Normalize SVG canvas to a small even outer border around content."""
    tree = ET.parse(output_path)
    root = tree.getroot()

    points = _svg_content_points(root)
    if not points:
        return

    # Graphviz wraps content in a transformed graph group. Account for that
    # transform so normalized viewBox bounds target actual rendered geometry.
    graph_tx, graph_ty = _svg_graph_translation(root)
    points = [(x + graph_tx, y + graph_ty) for x, y in points]

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x = min(xs)
    min_y = min(ys)
    max_x = max(xs)
    max_y = max(ys)

    width = max(1.0, (max_x - min_x) + 2.0 * padding)
    height = max(1.0, (max_y - min_y) + 2.0 * padding)
    view_min_x = min_x - padding
    view_min_y = min_y - padding

    root.attrib["viewBox"] = f"{view_min_x:.2f} {view_min_y:.2f} {width:.2f} {height:.2f}"
    if "width" in root.attrib:
        root.attrib["width"] = _format_svg_length(root.attrib["width"], width)
    if "height" in root.attrib:
        root.attrib["height"] = _format_svg_length(root.attrib["height"], height)

    _ensure_svg_white_background(root)
    _set_svg_background_rect(
        root,
        x=view_min_x,
        y=view_min_y,
        width=width,
        height=height,
    )

    _write_svg_tree(tree, output_path)


def _postprocess_direct_midpoint_edges_svg(*, output_path: Path) -> None:
    """Rewrite direct e/w edges to exact side-midpoint connectors."""
    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
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

        source_x = source_bounds[2] if source_side == "e" else source_bounds[0]
        source_y = (source_bounds[1] + source_bounds[3]) / 2.0
        target_x = target_bounds[0] if target_side == "w" else target_bounds[2]
        target_y = (target_bounds[1] + target_bounds[3]) / 2.0

        _set_edge_path(group, [(source_x, source_y), (target_x, target_y)])
        _set_arrow_polygon_horizontal(
            group,
            tip=(target_x, target_y),
            direction=(1 if target_x >= source_x else -1),
        )
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


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


def _normalize_node_backing_fills_svg(*, output_path: Path) -> None:
    """Remove Graphviz lightgrey backing polygons that read as drop shadows."""
    tree = ET.parse(output_path)
    root = tree.getroot()
    updated = False
    for group in root.iter():
        if group.attrib.get("class") != "node":
            continue
        for polygon in group.findall("{*}polygon"):
            fill = polygon.attrib.get("fill", "")
            stroke = polygon.attrib.get("stroke", "")
            if stroke != "none":
                continue
            if fill in {"lightgrey", "white", "#ffffff"}:
                polygon.attrib["fill"] = "#ffffff"
                polygon.attrib["fill-opacity"] = "1"
                updated = True
    if updated:
        _write_svg_tree(tree, output_path)


def _wrapped_sppm_boundary_pairs(dot: str) -> dict[str, tuple[str, str]]:
    """Extract wrapped LR SPPM boundary edges from DOT text.

    We key off the explicit route-plan attrs (arrowhead=none + minlen/penwidth)
    so postprocessing only touches the intended boundary doglegs.
    """
    first_leg: dict[str, str] = {}
    second_leg: dict[str, str] = {}
    for line in dot.splitlines():
        first_match = re.match(
            r'^\s*"(?P<source>[^"]+)" -> "(?P<anchor>__wrap_exit_lr_\d+)" \[.*arrowhead=none.*\];$',
            line,
        )
        if first_match:
            first_leg[first_match.group("anchor")] = first_match.group("source")
            continue

        second_match = re.match(
            r'^\s*"(?P<anchor>__wrap_exit_lr_\d+)" -> "(?P<target>[^"]+)" \[.*minlen=2.*penwidth=1\.2.*\];$',
            line,
        )
        if second_match:
            second_leg[second_match.group("anchor")] = second_match.group("target")

    return {
        anchor_id: (source_id, second_leg[anchor_id])
        for anchor_id, source_id in first_leg.items()
        if anchor_id in second_leg
    }


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


def _set_arrow_polygon(group: ET.Element, *, tip: tuple[float, float]) -> None:
    polygon = group.find("{*}polygon")
    if polygon is None:
        return
    tip_x, tip_y = tip
    polygon.attrib["points"] = (
        f"{tip_x:.2f},{tip_y:.2f} {tip_x - 4.0:.2f},{tip_y - 8.0:.2f} {tip_x + 4.0:.2f},{tip_y - 8.0:.2f} {tip_x:.2f},{tip_y:.2f}"
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


__all__ = ["render_dot_to_file"]
