"""SPPM-first publication plan builder backed by the shared publication model."""

from __future__ import annotations

from typing import Any

from ._process_header import extract_process_header_context
from ._publication import (
    PublicationBandContent,
    PublicationPlan,
    materialize_publication_series,
    PublicationPageSpec,
)
from ._sppm_projection import SppmProjectionContext
from ._sppm_publication_support import (
    _build_sppm_child_slots,
    _build_sppm_footer_content,
    _build_sppm_header_rows,
    _build_sppm_publication_canvas,
    _publication_diagnostics,
    _raise_for_publication_errors,
    _serialize_diagnostics,
)
from ._sppm_text import normalize_space
from .options import RenderOptions


def build_sppm_publication_plan(
    *,
    process: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    projection: SppmProjectionContext | None = None,
) -> PublicationPlan:
    """Build a renderer-independent single-page publication plan for SPPM output."""
    context = extract_process_header_context(process)
    title = normalize_space(context.title)
    show_header = options.sppm_show_header
    show_footer = options.sppm_show_footer
    projection_context = projection or SppmProjectionContext(
        requested_mode="top_level", effective_mode="top_level"
    )
    diagnostics = _publication_diagnostics(
        projection=projection_context, options=options
    )
    _raise_for_publication_errors(diagnostics)
    header_rows: list[tuple[str, str]] = []
    if show_header:
        header_rows = _build_sppm_header_rows(
            context=context,
            options=options,
            nodes=nodes,
            edges=edges,
            projection=projection_context,
            diagnostics=diagnostics,
        )
    footer_content = (
        _build_sppm_footer_content(context=context, options=options, nodes=nodes)
        if show_footer
        else None
    )
    canvas = _build_sppm_publication_canvas(
        title=title,
        footer_content=footer_content,
        options=options,
        show_header=show_header,
    )
    series = materialize_publication_series(
        series_id="main",
        title=title or "SPPM Publication",
        kind="map",
        page_specs=(
            PublicationPageSpec(
                page_key="p1",
                canvas=canvas,
                header_content=PublicationBandContent(
                    title=title, rows=tuple(header_rows)
                )
                if (show_header and title)
                else None,
                footer_content=footer_content,
                metadata={
                    "diagram": "sppm",
                    "publication_diagnostics": _serialize_diagnostics(diagnostics),
                    "page_format": options.publication_page_format,
                    "projection_mode": projection_context.effective_mode,
                    "requested_projection_mode": projection_context.requested_mode,
                    "focus_subprocess": projection_context.focus_subprocess,
                },
            ),
        ),
        metadata={
            "diagram": "sppm",
            "publication_diagnostics": _serialize_diagnostics(diagnostics),
            "page_format": options.publication_page_format,
            "projection_mode": projection_context.effective_mode,
            "requested_projection_mode": projection_context.requested_mode,
            "focus_subprocess": projection_context.focus_subprocess,
        },
    )
    return PublicationPlan(
        title=title,
        primary_series_id=series.series_id,
        series=(series,),
        artifact_slots=tuple(
            _build_sppm_child_slots(
                nodes=nodes,
                parent_series_id=series.series_id,
                focus_subprocess=projection_context.focus_subprocess,
            )
        ),
        metadata={
            "diagram": "sppm",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "projection_mode": projection_context.effective_mode,
            "publication_diagnostics": _serialize_diagnostics(diagnostics),
            "page_format": options.publication_page_format,
        },
    )
