"""SPPM-first publication plan builder backed by the shared publication model."""

from __future__ import annotations

from typing import Any

from flo.process.analysis import ProcessTimingAnalysis, analyze_process_timing
from flo.process.ir.models import IR

from .._process_header import extract_process_header_context
from .._publication import (
    PublicationBandContent,
    PublicationDiagnostic,
    PublicationFigureRef,
    PublicationPageSpec,
    PublicationPlan,
    materialize_publication_series,
)
from ..options import RenderOptions
from .projection import SppmProjectionContext
from .publication_support import (
    _build_sppm_child_slots,
    _build_sppm_footer_content,
    _build_sppm_header_rows,
    _build_sppm_publication_canvas,
    _publication_diagnostics,
    _raise_for_publication_errors,
    _serialize_diagnostics,
)
from .text import normalize_space


def build_sppm_publication_plan(
    *,
    process: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    projection: SppmProjectionContext | None = None,
    timing_analysis: ProcessTimingAnalysis | None = None,
) -> PublicationPlan:
    """Build a renderer-independent single-page publication plan for SPPM output."""
    context = extract_process_header_context(process)
    title = normalize_space(context.title)
    show_header = options.sppm_show_header
    show_footer = options.sppm_show_footer
    projection_context = projection or SppmProjectionContext(
        requested_mode="top_level", effective_mode="top_level"
    )
    diagnostics = (
        *_publication_diagnostics(projection=projection_context, options=options),
        *_pagination_diagnostics(nodes=nodes, edges=edges, options=options),
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
        _build_sppm_footer_content(
            context=context,
            options=options,
            nodes=nodes,
            timing_analysis=(
                timing_analysis
                if timing_analysis is not None
                else analyze_process_timing(process)
                if isinstance(process, IR)
                else None
            ),
        )
        if show_footer
        else None
    )
    canvas = _build_sppm_publication_canvas(
        title=title,
        header_rows=header_rows,
        footer_content=footer_content,
        options=options,
        show_header=show_header,
    )
    page_specs = _build_sppm_page_specs(
        canvas=canvas,
        title=title,
        header_rows=header_rows,
        footer_content=footer_content,
        nodes=nodes,
        edges=edges,
        options=options,
        projection=projection_context,
        diagnostics=diagnostics,
    )
    series = materialize_publication_series(
        series_id="main",
        title=title or "SPPM Publication",
        kind="map",
        page_specs=page_specs,
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


def _build_sppm_page_specs(
    *,
    canvas: Any,
    title: str,
    header_rows: list[tuple[str, str]],
    footer_content: PublicationBandContent | None,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    projection: SppmProjectionContext,
    diagnostics: tuple[Any, ...],
) -> tuple[PublicationPageSpec, ...]:
    node_id_pages = _sppm_page_node_ids(nodes, edges=edges, options=options)
    page_specs: list[PublicationPageSpec] = []
    page_count = len(node_id_pages)
    for page_number, node_ids in enumerate(node_id_pages, start=1):
        page_id = f"main-p{page_number}"
        metadata: dict[str, Any] = {
            "diagram": "sppm",
            "publication_diagnostics": _serialize_diagnostics(diagnostics),
            "page_format": options.publication_page_format,
            "projection_mode": projection.effective_mode,
            "requested_projection_mode": projection.requested_mode,
            "focus_subprocess": projection.focus_subprocess,
            "node_ids": node_ids,
        }
        if page_number > 1:
            metadata["continuation_from"] = f"main-p{page_number - 1}"
            metadata["continuation_from_step"] = node_id_pages[page_number - 2][-1]
        if page_number < page_count:
            metadata["continuation_to"] = f"main-p{page_number + 1}"
            metadata["continuation_to_step"] = node_id_pages[page_number][0]
        page_specs.append(
            PublicationPageSpec(
                page_key=f"p{page_number}",
                canvas=canvas,
                header_content=PublicationBandContent(
                    title=title, rows=tuple(header_rows)
                )
                if (options.sppm_show_header and title)
                else None,
                footer_content=footer_content,
                figures=(
                    PublicationFigureRef(
                        figure_id=f"{page_id}-figure",
                        asset_path=f"{page_id}.svg",
                        alt_text=f"{title or 'SPPM publication'} map page {page_number}",
                        source_node_ids=node_ids,
                    ),
                ),
                metadata=metadata,
            )
        )
    return tuple(page_specs)


def _sppm_page_node_ids(
    nodes: list[dict[str, Any]],
    *,
    edges: list[dict[str, Any]],
    options: RenderOptions,
) -> tuple[tuple[str, ...], ...]:
    node_ids = tuple(
        node_id for node in nodes if (node_id := str(node.get("id") or "").strip())
    )
    page_size = options.layout_target_columns or len(node_ids) or 1
    if options.layout_overflow != "paginate" or len(node_ids) <= page_size:
        return (node_ids,)
    linear_order = _linear_node_order(node_ids=node_ids, edges=edges)
    if linear_order is None:
        return (node_ids,)
    return tuple(
        linear_order[start : start + page_size]
        for start in range(0, len(linear_order), page_size)
    )


def _pagination_diagnostics(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    options: RenderOptions,
) -> tuple[PublicationDiagnostic, ...]:
    node_ids = tuple(
        node_id for node in nodes if (node_id := str(node.get("id") or "").strip())
    )
    page_size = options.layout_target_columns or len(node_ids) or 1
    if (
        options.layout_overflow != "paginate"
        or len(node_ids) <= page_size
        or _linear_node_order(node_ids=node_ids, edges=edges) is not None
    ):
        return ()
    strict = options.layout_fit == "fit-strict"
    return (
        PublicationDiagnostic(
            code="publication-pagination-fallback",
            severity="error" if strict else "warning",
            message=(
                "Requested publication pagination fell back to a single page "
                "because cross-page continuation is ambiguous for non-linear flow."
            ),
            metadata={
                "requested_mode": "paginate",
                "effective_mode": "single_page",
                "fallback_reason": "ambiguous-non-linear-continuation",
                "strict": strict,
            },
        ),
    )


def _linear_node_order(
    *, node_ids: tuple[str, ...], edges: list[dict[str, Any]]
) -> tuple[str, ...] | None:
    """Return semantic path order only when the visible graph is one linear path."""
    if len(node_ids) <= 1:
        return node_ids
    graph = _build_linear_graph(node_ids=node_ids, edges=edges)
    if graph is None:
        return None
    successors, indegree = graph
    start = _linear_start_node(indegree)
    if start is None:
        return None
    ordered = _walk_linear_path(start=start, successors=successors)
    return ordered if len(ordered) == len(node_ids) else None


def _build_linear_graph(
    *, node_ids: tuple[str, ...], edges: list[dict[str, Any]]
) -> tuple[dict[str, str | None], dict[str, int]] | None:
    visible_ids = set(node_ids)
    if len(visible_ids) != len(node_ids) or len(edges) != len(node_ids) - 1:
        return None
    successors: dict[str, str | None] = dict.fromkeys(node_ids)
    indegree = dict.fromkeys(node_ids, 0)
    for edge in edges:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if source not in visible_ids or target not in visible_ids:
            return None
        if successors[source] is not None or indegree[target] > 0:
            return None
        successors[source] = target
        indegree[target] += 1
    return successors, indegree


def _linear_start_node(indegree: dict[str, int]) -> str | None:
    starts = tuple(node_id for node_id, degree in indegree.items() if degree == 0)
    return starts[0] if len(starts) == 1 else None


def _walk_linear_path(
    *, start: str, successors: dict[str, str | None]
) -> tuple[str, ...]:
    ordered: list[str] = []
    visited: set[str] = set()
    current: str | None = start
    while current is not None and current not in visited:
        ordered.append(current)
        visited.add(current)
        current = successors[current]
    return tuple(ordered)
