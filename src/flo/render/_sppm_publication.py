"""SPPM-first publication plan builder backed by the shared publication model."""

from __future__ import annotations

from typing import Any

from flo.services.errors import RenderError

from ._process_header import extract_process_header_context
from ._publication import (
    PublicationBandContent,
    PublicationBounds,
    PublicationDiagnostic,
    PublicationMargins,
    PublicationPlan,
    build_publication_canvas,
    build_publication_canvas_for_format,
    evaluate_publication_fallback,
    materialize_publication_series,
    PublicationPageSpec,
)
from ._sppm_projection import SppmProjectionContext
from ._sppm_publication_support import (
    _build_sppm_child_slots,
    _build_sppm_footer_content,
    _build_sppm_header_rows,
)
from ._sppm_text import normalize_space
from .options import RenderOptions

_DEFAULT_SPPM_PUBLICATION_WIDTH_PX = 1200
_DEFAULT_SPPM_PUBLICATION_MARGINS = PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48)
_SPPM_HEADER_BAND_HEIGHT_PX = 96


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
    projection_context = projection or SppmProjectionContext(requested_mode="top_level", effective_mode="top_level")
    diagnostics = _publication_diagnostics(projection=projection_context, options=options)
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
    footer_content = _build_sppm_footer_content(context=context, options=options) if show_footer else None
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
                header_content=PublicationBandContent(title=title, rows=tuple(header_rows)) if (show_header and title) else None,
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


def _build_sppm_publication_canvas(
    *,
    title: str,
    footer_content: PublicationBandContent | None,
    options: RenderOptions,
    show_header: bool,
) -> Any:
    header_height_px = _SPPM_HEADER_BAND_HEIGHT_PX if (show_header and title) else 0
    footer_height_px = 72 if footer_content is not None else 0
    if options.publication_page_format:
        return build_publication_canvas_for_format(
            page_format=options.publication_page_format,
            header_height_px=header_height_px,
            footer_height_px=footer_height_px,
            width_px_override=options.layout_max_width_px,
        )
    return build_publication_canvas(
        bounds=PublicationBounds(width_px=options.layout_max_width_px or _DEFAULT_SPPM_PUBLICATION_WIDTH_PX),
        margins=_DEFAULT_SPPM_PUBLICATION_MARGINS,
        header_height_px=header_height_px,
        footer_height_px=footer_height_px,
    )


def _publication_diagnostics(
    *,
    projection: SppmProjectionContext,
    options: RenderOptions,
) -> tuple[PublicationDiagnostic, ...]:
    return evaluate_publication_fallback(
        requested_mode=projection.requested_mode,
        effective_mode=projection.effective_mode,
        fallback_reason=projection.fallback_reason,
        strict=options.layout_fit == "fit-strict",
    )


def _raise_for_publication_errors(diagnostics: tuple[PublicationDiagnostic, ...]) -> None:
    errors = [diagnostic.message for diagnostic in diagnostics if diagnostic.severity == "error"]
    if errors:
        raise RenderError("; ".join(errors))


def _serialize_diagnostics(diagnostics: tuple[PublicationDiagnostic, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "code": diagnostic.code,
            "severity": diagnostic.severity,
            "message": diagnostic.message,
            **diagnostic.metadata,
        }
        for diagnostic in diagnostics
    )

