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
from typing import TYPE_CHECKING

from flo.services._svg_utils import (
    _svg_node_outer_bounds,
    _svg_node_bounds,
    _svg_edge_groups,
    _svg_content_points,
    _set_svg_background_rect,
    _ensure_svg_white_background,
    _svg_graph_translation,
    _format_svg_length,
    _set_edge_path,
    _set_arrow_polygon,
    _set_arrow_polygon_horizontal,
    _write_svg_tree,
)
from flo.services.errors import RenderError

if TYPE_CHECKING:
    from flo.render._sppm_postprocess_contract import SppmSvgPostprocessContract

_SUPPORTED_FORMATS = {"png", "svg", "pdf", "eps", "ps"}
_SVG_OUTER_PADDING_PX = 6.0
_SVG_NS = "http://www.w3.org/2000/svg"



def render_dot_to_file(
    dot: str,
    output_path: str,
    sppm_contract: SppmSvgPostprocessContract | None = None,
) -> None:
    """Render DOT source to an image file via the system `dot` binary.

    The output format is inferred from the file extension.  Supported
    extensions: ``.png``, ``.svg``, ``.pdf``, ``.eps``, ``.ps``.
    Pass *sppm_contract* to enable contract-based SVG edge rewriting instead
    of fragile regex matching.

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

    dot_for_render = dot

    try:
        result = subprocess.run(
            ["dot", f"-T{fmt}", "-o", output_path],
            input=dot_for_render,
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
        # Two-pass SPPM anchor pinning: re-render SVG with exact anchor positions
        # derived from pass-1 layout.  Only activates when SPPM return-loop anchors
        # are detected; otherwise the SVG written above is already final.
        _postprocess_sppm_return_loop_edges_svg(dot=dot, output_path=svg_path, contract=sppm_contract)
        _postprocess_sppm_branch_edges_svg(dot=dot, output_path=svg_path, contract=sppm_contract)
        _postprocess_sppm_rework_labels_svg(dot=dot, output_path=svg_path, contract=sppm_contract)
        _postprocess_wrapped_sppm_svg(dot=dot, output_path=svg_path, contract=sppm_contract)
        _postprocess_queue_baseline_alignment_svg(output_path=svg_path)
        _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
        _normalize_node_backing_fills_svg(output_path=svg_path)
        _normalize_svg_outer_padding(output_path=svg_path, padding=_SVG_OUTER_PADDING_PX)


def _postprocess_sppm_return_loop_edges_svg(
    *,
    dot: str,
    output_path: Path,
    contract: SppmSvgPostprocessContract | None = None,
) -> None:
    """Rewrite SPPM return-loop edge paths to exact L-shapes.

    Graphviz routes return-loop corridor edges with an extra dogleg because it
    places the invisible anchor node at an intermediate Y between the rework
    node and its target.  After Graphviz produces the SVG (with correct node
    positions and sizes), we read the rendered node bounds and rewrite just the
    two return-loop path segments to a clean L-shape: one horizontal segment
    from the source's left edge to the target's center X, then one vertical
    segment down into the target's south port.

    Scope:
    - Only ``__sppm_rework_corridor_*`` return-loop edges (tailport=w source,
      headport=s target).
    - Only SVG output.
    """
    specs = _collect_return_anchor_specs(dot=dot, contract=contract)
    if not specs:
        return

    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    edge_groups = _svg_edge_groups(root)
    updated = False

    for source_id, anchor_id, target_id in specs:
        first_group, first_source_side, _first_target_side = _find_rework_edge_group(
            edge_groups=edge_groups,
            source_id=source_id,
            target_id=anchor_id,
        )
        second_group, _second_source_side, second_target_side = _find_rework_edge_group(
            edge_groups=edge_groups,
            source_id=anchor_id,
            target_id=target_id,
        )
        if first_group is None or second_group is None:
            continue

        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        if source_bounds is None:
            continue

        _ = first_source_side
        # Return-loop policy: always exit the rework node from west face.
        source_point = _point_on_bounds(source_bounds, "w")
        if target_bounds is not None:
            # Return-loop policy: always rejoin main line at target south face.
            target_point = _point_on_bounds(target_bounds, "s")
        else:
            _start, fallback_end = _edge_path_start_end(second_group)
            if fallback_end is None:
                continue
            target_point = fallback_end
        source_x, source_y = source_point
        target_x, target_y = target_point
        # Compute the corner: X of target, Y of source midpoint.
        corner_x = target_x
        corner_y = source_y

        _set_edge_path(
            first_group,
            [
                (source_x, source_y),
                (corner_x, corner_y),
            ],
        )
        _set_edge_path(
            second_group,
            [
                (corner_x, corner_y),
                (target_x, target_y),
            ],
        )
        # Arrowhead should point into the target's south face.
        _set_arrow_polygon(second_group, tip=(target_x, target_y), direction=1)
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _postprocess_sppm_branch_edges_svg(
    *,
    dot: str,
    output_path: Path,
    contract: SppmSvgPostprocessContract | None = None,
) -> None:
    specs = _collect_branch_anchor_specs(dot=dot, contract=contract)
    if not specs:
        return

    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    edge_groups = _svg_edge_groups(root)
    updated = False

    for source_id, anchor_id, target_id in specs:
        first_group, first_source_side, _first_target_side = _find_rework_edge_group(
            edge_groups=edge_groups,
            source_id=source_id,
            target_id=anchor_id,
        )
        second_group, _second_source_side, second_target_side = _find_rework_edge_group(
            edge_groups=edge_groups,
            source_id=anchor_id,
            target_id=target_id,
        )
        if first_group is None or second_group is None:
            continue

        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        if source_bounds is None or target_bounds is None:
            continue

        source_x, source_y = _point_on_bounds(source_bounds, first_source_side)
        target_x, target_y = _point_on_bounds(target_bounds, second_target_side)
        # Corner: midpoint Y between source bottom and target top.
        corner_y = (source_y + target_y) / 2.0

        _set_edge_path(
            first_group,
            [
                (source_x, source_y),
                (source_x, corner_y),
            ],
        )
        _set_edge_path(
            second_group,
            [
                (source_x, corner_y),
                (target_x, target_y),
            ],
        )
        _set_arrow_for_side(second_group, tip=(target_x, target_y), side=second_target_side)
        updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _postprocess_sppm_rework_labels_svg(
    *,
    dot: str,
    output_path: Path,
    contract: SppmSvgPostprocessContract | None = None,
) -> None:
    """Reposition rework annotation boxes beside their source nodes.

    Graphviz places taillabel geometry based on spline heuristics, which drifts
    noticeably once the loop spans multiple rows. After the main edge rewrite
    pass has fixed the branch/return paths, this pass moves the rendered label
    box polygon/text as a unit relative to the source node's rendered bounds.
    """
    branch_specs = _collect_branch_anchor_specs(dot=dot, contract=contract)
    return_specs = _collect_return_anchor_specs(dot=dot, contract=contract)
    if not branch_specs and not return_specs:
        return

    tree = ET.parse(output_path)
    root = tree.getroot()
    node_bounds = _svg_node_outer_bounds(root)
    edge_groups = _svg_edge_groups(root)
    updated = False

    for source_id, anchor_id, _target_id in branch_specs:
        group = edge_groups.get(f"{source_id}:s->{anchor_id}")
        source_bounds = node_bounds.get(source_id)
        if group is None or source_bounds is None:
            continue
        label_bounds = _svg_edge_label_bounds(group)
        if label_bounds is None:
            continue
        target_left = source_bounds[2] + 8.0
        target_top = source_bounds[3] + 2.0
        if _reposition_svg_edge_label(group, left=target_left, top=target_top):
            updated = True

    for source_id, anchor_id, _target_id in return_specs:
        group = edge_groups.get(f"{source_id}:w->{anchor_id}")
        source_bounds = node_bounds.get(source_id)
        if group is None or source_bounds is None:
            continue
        label_bounds = _svg_edge_label_bounds(group)
        if label_bounds is None:
            continue
        width = label_bounds[2] - label_bounds[0]
        target_left = source_bounds[0] - width - 10.0
        target_top = source_bounds[1] + 8.0
        if _reposition_svg_edge_label(group, left=target_left, top=target_top):
            updated = True

    if updated:
        _write_svg_tree(tree, output_path)


def _collect_return_anchor_specs(
    *,
    dot: str,
    contract: SppmSvgPostprocessContract | None,
):
    _ = dot
    if contract and contract.rework_return_edges:
        specs = []
        for edge in contract.rework_return_edges:
            anchor_id = getattr(edge, "anchor_id", None)
            if not anchor_id:
                continue
            specs.append((edge.source_id, anchor_id, edge.target_id))
        return specs

    return []


def _collect_branch_anchor_specs(
    *,
    dot: str,
    contract: SppmSvgPostprocessContract | None,
):
    _ = dot
    if contract and contract.rework_branch_edges:
        specs = []
        for edge in contract.rework_branch_edges:
            anchor_id = getattr(edge, "anchor_id", None)
            if not anchor_id:
                continue
            specs.append((edge.source_id, anchor_id, edge.target_id))
        return specs

    return []


def _find_rework_edge_group(
    *,
    edge_groups: dict[str, ET.Element],
    source_id: str,
    target_id: str,
) -> tuple[ET.Element | None, str, str]:
    best: tuple[ET.Element | None, str, str, int] = (None, "e", "w", -1)
    for title, group in edge_groups.items():
        parsed = _parse_edge_title_for_ids(title=title, source_id=source_id, target_id=target_id)
        if parsed is None:
            continue
        source_side, target_side = parsed
        score = int(source_side in {"n", "s", "e", "w"}) + int(target_side in {"n", "s", "e", "w"})
        if score > best[3]:
            best = (group, source_side, target_side, score)
            if score == 2:
                break

    return best[0], best[1], best[2]


def _parse_edge_title_for_ids(*, title: str, source_id: str, target_id: str) -> tuple[str, str] | None:
    if "->" not in title:
        return None
    left, right = title.split("->", 1)
    if not _endpoint_matches_node_id(left, source_id):
        return None
    if not _endpoint_matches_node_id(right, target_id):
        return None
    return (_endpoint_compass_side(left), _endpoint_compass_side(right))


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


def _set_arrow_for_side(group: ET.Element, *, tip: tuple[float, float], side: str) -> None:
    if side == "w":
        _set_arrow_polygon_horizontal(group, tip=tip, direction=-1)
        return
    if side == "e":
        _set_arrow_polygon_horizontal(group, tip=tip, direction=1)
        return
    if side == "s":
        _set_arrow_polygon(group, tip=tip, direction=1)
        return
    _set_arrow_polygon(group, tip=tip, direction=-1)


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


def _svg_edge_label_bounds(group: ET.Element) -> tuple[float, float, float, float] | None:
    polygons = _svg_edge_label_polygons(group)
    if not polygons:
        return None
    points: list[tuple[float, float]] = []
    for polygon in polygons:
        raw_points = polygon.attrib.get("points", "")
        for token in raw_points.split():
            if "," not in token:
                continue
            x_text, y_text = token.split(",", 1)
            points.append((float(x_text), float(y_text)))
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _svg_edge_label_polygons(group: ET.Element) -> list[ET.Element]:
    polygons: list[ET.Element] = []
    for polygon in group.findall("{*}polygon"):
        fill = polygon.attrib.get("fill", "")
        stroke = polygon.attrib.get("stroke", "")
        if stroke == "#666666" or (fill == "#ffffff" and stroke == "none"):
            polygons.append(polygon)
    return polygons


def _reposition_svg_edge_label(group: ET.Element, *, left: float, top: float) -> bool:
    bounds = _svg_edge_label_bounds(group)
    if bounds is None:
        return False
    dx = left - bounds[0]
    dy = top - bounds[1]
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return False

    for polygon in _svg_edge_label_polygons(group):
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

    return True

def _postprocess_wrapped_sppm_svg(
    *,
    dot: str,
    output_path: Path,
    contract: SppmSvgPostprocessContract | None = None,
) -> None:
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
    
    # Use contract-based edge lookup if available; otherwise fall back to regex DOT scanning.
    if contract and contract.wrapped_boundary_edges:
        boundary_pairs: dict[str, tuple[str, str]] = {}
        for idx, edge in enumerate(contract.wrapped_boundary_edges):
            anchor_id = getattr(edge, "anchor_id", None) or f"__wrap_exit_lr_{idx}"
            boundary_pairs[anchor_id] = (edge.source_id, edge.target_id)
    else:
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


def _should_skip_edge_rewrite(
    group: ET.Element,
    source_y: float,
    target_y: float,
) -> bool:
    """Check if edge should be skipped (already horizontal at correct Y)."""
    start_point, end_point = _edge_path_start_end(group)
    if start_point is None or end_point is None:
        return False
    # Skip only if: already horizontal AND at the correct Y coordinates.
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
    """Compute edge endpoints with triangle side-midpoint attachment.
    
    Returns: (source_x, source_y, target_x, target_y)
    """
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

    # For queue triangle attachments, align horizontally by snapping the
    # opposite endpoint's Y to match the triangle's side-midpoint.
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
    """Align horizontal edges when triangles are attached.
    
    Returns: (adjusted_source_y, adjusted_target_y) to keep edge horizontal
    """
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
        if fill != "#ff9800" or stroke_l != "#e65100":
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
            r'^\s*"(?P<source>[^"]+)"(?::"[^"]*":\w+)? -> "(?P<anchor>__wrap_exit_lr_\d+)" \[.*arrowhead=none.*\];$',
            line,
        )
        if first_match:
            first_leg[first_match.group("anchor")] = first_match.group("source")
            continue

        second_match = re.match(
            r'^\s*"(?P<anchor>__wrap_exit_lr_\d+)" -> "(?P<target>[^"]+)"(?::"[^"]*":\w+)? \[.*minlen=2.*penwidth=1\.2.*\];$',
            line,
        )
        if second_match:
            second_leg[second_match.group("anchor")] = second_match.group("target")

    return {
        anchor_id: (source_id, second_leg[anchor_id])
        for anchor_id, source_id in first_leg.items()
        if anchor_id in second_leg
    }


__all__ = ["render_dot_to_file"]
