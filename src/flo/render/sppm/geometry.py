"""SPPM-owned finalization of node, route, visible-lane, and canvas geometry."""

from .._execution import RoutedGeometry
from ..layout_core.models import LayoutResult
from ..layout_core.rework_geometry import infer_rework_row_ids
from .namespace import is_synthetic_sppm_lane
from .rows import (
    _display_canvas_bounds,
    _enforce_sppm_row_alignment,
    _orthogonalized_edges,
    rework_alignment_diagnostics,
    row_gap_diagnostics,
)


def _display_geometry(result):
    if result.orientation == "tb":
        return dict(result.node_bounds), _orthogonalized_edges(
            edge_paths=result.edge_paths
        )
    return _enforce_sppm_row_alignment(
        node_bounds=result.node_bounds, edge_paths=result.edge_paths, lanes=result.lanes
    )


def _uses_horizontal_row_alignment(result):
    return result.orientation != "tb" and not any(
        str(getattr(lane, "id", "")).startswith("__sppm_row_wrap_")
        for lane in result.lanes
    )


def finalize_sppm_geometry(result: LayoutResult) -> RoutedGeometry:
    """Finalize inspectable diagram geometry without mutating engine geometry."""
    nodes, paths = _display_geometry(result)
    diagnostics = list(result.diagnostics)
    if _uses_horizontal_row_alignment(result):
        diagnostics.extend(
            row_gap_diagnostics(node_bounds=nodes, lanes=result.lanes, edge_paths=paths)
        )
        diagnostics.extend(
            rework_alignment_diagnostics(
                node_bounds=nodes, lanes=result.lanes, edge_paths=paths
            )
        )
    _, correction = infer_rework_row_ids(
        node_ids=set(nodes),
        edges=(
            (a, b, path.is_rework, path.rework_variant)
            for (a, b), path in paths.items()
        ),
    )
    return RoutedGeometry(
        diagram="sppm",
        node_bounds=nodes,
        edge_paths=paths,
        lanes=tuple(
            lane for lane in result.lanes if not is_synthetic_sppm_lane(lane.id)
        ),
        canvas_bounds=_display_canvas_bounds(
            base_canvas=result.canvas_bounds, node_bounds=nodes, edge_paths=paths
        ),
        node_groups={
            "mainline": frozenset(set(nodes) - correction),
            "correction": frozenset(correction),
        },
        edge_groups={
            "correction": frozenset(
                (a, b) for a, b in paths if a in correction and b in correction
            )
        },
        diagnostics=tuple(diagnostics),
    )
