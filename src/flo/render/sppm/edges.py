"""Explicit route-to-edge adapter; production emission consumes finalized scenes."""

from __future__ import annotations

from typing import Any

from ..options import RenderOptions
from .edge_geometry import prepare_edge, prepare_token
from .edge_svg import emit_annotation, emit_edge


def _edge_svg(edge_path: Any, *, options: RenderOptions | None = None, **kwargs):
    """Finalize one precomputed route and emit it for stage-level consumers."""
    edge = prepare_edge(
        edge_path, options=options or RenderOptions(diagram="sppm"), **kwargs
    )
    return emit_edge(edge, options or RenderOptions(diagram="sppm")), tuple(
        a.bounds for a in edge.annotations
    )


def _edge_token_svg(
    *,
    points: Any,
    token: str,
    near_source: bool,
    options: RenderOptions | None = None,
    avoid_bounds=(),
    canvas_bounds=None,
    diagnostics=None,
    annotation_bounds=None,
):
    """Finalize one token for explicit stage-level consumers."""
    annotation = prepare_token(
        points, token, near_source, avoid_bounds, canvas_bounds, diagnostics
    )
    if annotation_bounds is not None:
        annotation_bounds.append(annotation.bounds)
    return emit_annotation(annotation, options or RenderOptions(diagram="sppm"))
