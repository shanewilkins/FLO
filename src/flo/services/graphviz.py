"""Graphviz rendering service for FLO.

Provides a thin wrapper around the system `dot` binary that converts DOT
source into an image file.  The DOT pipeline is kept as a separate step so
that FLO's core rendering logic never depends on Graphviz being installed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from flo.services.errors import RenderError

_SUPPORTED_FORMATS = {"png", "svg", "pdf", "eps", "ps"}


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

    # Graphviz ortho routing does not reliably honor the intended wrapped SPPM
    # dogleg landing geometry (especially top-center entry on boundary edges).
    # We keep DOT as the logical routing contract, then finalize those boundary
    # polylines in SVG where node bounds are known and stable.
    if fmt == "svg":
        _postprocess_wrapped_sppm_svg(dot=dot, output_path=Path(output_path))


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
        corridor_x = max(source_right + 24.0, target_center_x + 24.0)

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
        tree.write(output_path, encoding="utf-8", xml_declaration=True)


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


__all__ = ["render_dot_to_file"]
