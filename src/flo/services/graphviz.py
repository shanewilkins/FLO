"""Graphviz rendering service for FLO.

Provides a thin wrapper around the system `dot` binary that converts DOT
source into an image file.  The DOT pipeline is kept as a separate step so
that FLO's core rendering logic never depends on Graphviz being installed.

This service remains in place as a deprecated compatibility-only path while
direct SVG rendering and export surfaces take precedence.
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
    _write_svg_tree,
)
from flo.services._graphviz_direct_midpoint import (
    _postprocess_direct_midpoint_edges_svg,
    _postprocess_queue_baseline_alignment_svg,
)
from flo.services._graphviz_decision_labels import (
    postprocess_sppm_decision_outcome_labels_svg,
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

    # SVG gets a small FLO-owned postprocess compatibility layer:
    # 1) normalize wrapped SPPM boundary doglegs where Graphviz can drift;
    # 2) normalize outer SVG padding so borders are small and even.
    # Rework branch/return path geometry is owned by ELK/SVG direct rendering.
    # Future work: extend similar canvas normalization to non-SVG formats.
    if fmt == "svg":
        svg_path = Path(output_path)
        if not svg_path.exists():
            return
        _postprocess_sppm_rework_labels_svg(
            dot=dot, output_path=svg_path, contract=sppm_contract
        )
        postprocess_sppm_decision_outcome_labels_svg(
            output_path=svg_path, contract=sppm_contract
        )
        _postprocess_wrapped_sppm_svg(
            dot=dot, output_path=svg_path, contract=sppm_contract
        )
        _postprocess_queue_baseline_alignment_svg(output_path=svg_path)
        _postprocess_direct_midpoint_edges_svg(output_path=svg_path)
        _normalize_node_backing_fills_svg(output_path=svg_path)
        _normalize_svg_outer_padding(
            output_path=svg_path, padding=_SVG_OUTER_PADDING_PX
        )


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


def _edge_path_start_end(
    group: ET.Element,
) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    path = group.find("{*}path")
    if path is None:
        return None, None
    d = path.attrib.get("d", "")
    coords = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", d)]
    points = [(coords[idx], coords[idx + 1]) for idx in range(0, len(coords) - 1, 2)]
    if not points:
        return None, None
    return points[0], points[-1]


def _svg_edge_label_bounds(
    group: ET.Element,
) -> tuple[float, float, float, float] | None:
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

    tree = ET.parse(output_path)
    root = tree.getroot()

    node_bounds = _svg_node_bounds(root)
    edge_groups = _svg_edge_groups(root)

    # Use contract-based edge lookup if available; otherwise fall back to regex DOT scanning.
    boundary_pairs: dict[str, tuple[str, str]]
    if contract and contract.wrapped_boundary_edges:
        boundary_pairs = {}
        for edge in contract.wrapped_boundary_edges:
            source_id = edge.source_id
            target_id = edge.target_id
            anchor_id = getattr(edge, "anchor_id", None)
            if not anchor_id:
                anchor_id = _find_wrap_exit_anchor_id(
                    edge_groups=edge_groups,
                    source_id=source_id,
                    target_id=target_id,
                )
            if not anchor_id:
                continue
            boundary_pairs[anchor_id] = (source_id, target_id)
    else:
        boundary_pairs = _wrapped_sppm_boundary_pairs(dot)

    if not boundary_pairs:
        return

    updated = False

    for anchor_id, (source_id, target_id) in boundary_pairs.items():
        source_bounds = node_bounds.get(source_id)
        target_bounds = node_bounds.get(target_id)
        first_group = edge_groups.get(f"{source_id}:e->{anchor_id}")
        second_group = edge_groups.get(f"{anchor_id}->{target_id}:s")
        if second_group is None:
            second_group = edge_groups.get(f"{anchor_id}->{target_id}:n")
        if (
            source_bounds is None
            or target_bounds is None
            or first_group is None
            or second_group is None
        ):
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


def _find_wrap_exit_anchor_id(
    *,
    edge_groups: dict[str, ET.Element],
    source_id: str,
    target_id: str,
) -> str | None:
    for title in edge_groups.keys():
        match = re.fullmatch(
            rf"{re.escape(source_id)}:e->(?P<anchor>__wrap_exit_lr_\d+)",
            title,
        )
        if not match:
            continue
        anchor_id = match.group("anchor")
        if (
            f"{anchor_id}->{target_id}:s" in edge_groups
            or f"{anchor_id}->{target_id}:n" in edge_groups
        ):
            return anchor_id
    return None


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

    root.attrib["viewBox"] = (
        f"{view_min_x:.2f} {view_min_y:.2f} {width:.2f} {height:.2f}"
    )
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
