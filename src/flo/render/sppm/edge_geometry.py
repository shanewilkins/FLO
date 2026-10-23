"""Finalize shape attachments and ordered edge annotations before SVG emission."""

from __future__ import annotations

from typing import Any

from .._diagnostics import RenderDiagnostic
from .._execution import AttachedEdge, EdgeAnnotation, PositionedText
from ..options import RenderOptions
from .attachments import _clip_edge_points_to_node_bounds, _normalize_rework_edge_points
from .edge_layout import (
    _annotation_bounds_for_placement,
    _avoid_bounds_overlap,
    _edge_callout_placement,
    _edge_token_placement,
    _resolve_edge_label_placement,
)


def prepare_edge(
    edge_path: Any,
    *,
    options: RenderOptions,
    source_bounds=None,
    target_bounds=None,
    source_kind="task",
    target_kind="task",
    avoid_bounds=(),
    canvas_bounds=None,
    diagnostics=None,
    render_as_rework_style=False,
) -> AttachedEdge:
    """Attach one route and resolve its annotations in stable occupancy order."""
    rework = bool(edge_path.is_rework or render_as_rework_style)
    points = _clip_edge_points_to_node_bounds(
        _normalize_rework_edge_points(
            edge_path.points,
            is_rework=rework,
            rework_variant=str(edge_path.rework_variant or ""),
        ),
        source_bounds=source_bounds,
        source_kind=source_kind,
        target_bounds=target_bounds,
        target_kind=target_kind,
        diagnostics=diagnostics,
        edge_id=f"{edge_path.edge[0]}->{edge_path.edge[1]}",
    )
    annotations = []
    if len(points) < 2:
        return AttachedEdge(
            edge_path.edge, points, rework, str(edge_path.rework_variant or "")
        )
    if edge_path.label:
        width = max(28.0, float(len(edge_path.label) * 7.0))
        placement = _resolve_edge_label_placement(
            edge_path=edge_path,
            points=points,
            rework_edge=rework,
            rework_variant=str(edge_path.rework_variant or ""),
            source_kind=source_kind,
            avoid_bounds=avoid_bounds,
            label_width=width,
            canvas_bounds=canvas_bounds,
            diagnostics=diagnostics,
        )
        annotations.append(
            EdgeAnnotation(
                "label",
                _annotation_bounds_for_placement(
                    placement, box_width=width, box_height=18
                ),
                (
                    PositionedText(
                        edge_path.label, placement.x, placement.y + 1, placement.anchor
                    ),
                ),
            )
        )
    if edge_path.callout_lines:
        annotations.append(
            _prepare_callout(
                edge_path,
                points,
                rework,
                options,
                avoid_bounds + tuple(a.bounds for a in annotations),
                canvas_bounds,
                diagnostics,
            )
        )
    for token, near_source in (
        (edge_path.outgoing_token, True),
        (edge_path.incoming_token, False),
    ):
        if token:
            annotations.append(
                prepare_token(
                    points,
                    str(token),
                    near_source,
                    avoid_bounds + tuple(a.bounds for a in annotations),
                    canvas_bounds,
                    diagnostics,
                )
            )
    return AttachedEdge(
        edge_path.edge,
        points,
        rework,
        str(edge_path.rework_variant or ""),
        tuple(annotations),
    )


def _prepare_callout(path, points, rework, options, avoid, canvas, diagnostics):
    lines = path.callout_lines
    width = max(88.0, float(max(len(line) for line in lines) * 6.7) + 18.0)
    height = 12.0 + len(lines) * 14.0
    placement = _edge_callout_placement(
        points,
        near_source=bool(path.callout_near_source),
        has_label=bool(path.label),
        rework_edge=rework,
        avoid_bounds=avoid,
        box_width=width,
        box_height=height,
        canvas_bounds=canvas,
        diagnostics=diagnostics,
        diagnostic_context={
            "annotation_kind": "edge_callout",
            "edge": f"{path.edge[0]}->{path.edge[1]}",
        },
    )
    box = _annotation_bounds_for_placement(
        placement, box_width=width, box_height=height
    )
    texts = []
    y = box.y_px + 15.0
    for line in lines:
        for subline in (segment for segment in line.split("\n") if segment):
            texts.append(PositionedText(subline, placement.x, y, "middle", 10, "400"))
            y += 14.0 * options.resolved_theme.typography_scale
    return EdgeAnnotation("callout", box, tuple(texts))


def prepare_token(
    points,
    token: str,
    near_source: bool,
    avoid_bounds=(),
    canvas_bounds=None,
    diagnostics: list[RenderDiagnostic] | None = None,
) -> EdgeAnnotation:
    """Resolve a continuation token's rectangle and text baseline."""
    width = max(42.0, float(len(token) * 7.2) + 16.0)
    placement = _avoid_bounds_overlap(
        _edge_token_placement(points, near_source=near_source),
        box_width=width,
        box_height=22,
        avoid_bounds=avoid_bounds,
        canvas_bounds=canvas_bounds,
        segment_dx=1,
        segment_dy=0,
        diagnostics=diagnostics,
        diagnostic_context={"annotation_kind": "edge_token", "token": token},
    )
    return EdgeAnnotation(
        "token",
        _annotation_bounds_for_placement(placement, box_width=width, box_height=22),
        (
            PositionedText(
                token, placement.x, placement.y + 3, "middle", 9, "600", "detail_text"
            ),
        ),
        token,
        "source" if near_source else "target",
    )
