"""SPPM-first publication plan builder backed by the shared publication model."""

from __future__ import annotations

from typing import Any

from flo.compiler.ir.subprocess_refs import resolve_subprocess_detail_map_reference

from ._process_header import build_process_header_rows, extract_process_header_context
from ._publication import (
    PublicationArtifactSlot,
    PublicationBandContent,
    PublicationBounds,
    PublicationMargins,
    PublicationPage,
    PublicationPlan,
    PublicationSeries,
    build_publication_bands,
    build_publication_canvas,
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
) -> PublicationPlan:
    """Build a renderer-independent single-page publication plan for SPPM output."""
    context = extract_process_header_context(process)
    title = normalize_space(context.title)
    header_rows = _build_sppm_header_rows(context=context, options=options, nodes=nodes, edges=edges)
    footer_content = _build_sppm_footer_content(context=context, options=options)
    canvas = build_publication_canvas(
        bounds=PublicationBounds(width_px=options.layout_max_width_px or _DEFAULT_SPPM_PUBLICATION_WIDTH_PX),
        margins=_DEFAULT_SPPM_PUBLICATION_MARGINS,
        header_height_px=_SPPM_HEADER_BAND_HEIGHT_PX if title else 0,
        footer_height_px=72 if footer_content is not None else 0,
    )
    page = PublicationPage(
        page_id="main-p1",
        page_number=1,
        series_id="main",
        canvas=canvas,
        bands=build_publication_bands(
            canvas=canvas,
            header_content=PublicationBandContent(title=title, rows=tuple(header_rows)) if title else None,
            footer_content=footer_content,
        ),
        metadata={
            "diagram": "sppm",
            "projection_mode": options.subprocess_view,
        },
    )
    series = PublicationSeries(
        series_id="main",
        title=title or "SPPM Publication",
        kind="map",
        pages=(page,),
        metadata={
            "diagram": "sppm",
            "projection_mode": options.subprocess_view,
            "page_count": 1,
        },
    )
    return PublicationPlan(
        title=title,
        primary_series_id=series.series_id,
        series=(series,),
        artifact_slots=tuple(_build_sppm_child_slots(nodes=nodes, parent_series_id=series.series_id)),
        metadata={
            "diagram": "sppm",
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    )


def _build_sppm_header_rows(
    *,
    context: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    extra_rows: list[tuple[str, str]] = []
    if options.sppm_output_profile != "default":
        extra_rows.append(("Profile", options.sppm_output_profile))
    if options.subprocess_view != "expanded":
        extra_rows.append(("Subprocess View", options.subprocess_view.replace("_", "-")))
    extra_rows.append(("Nodes", str(len(nodes))))
    extra_rows.append(("Edges", str(len(edges))))
    return build_process_header_rows(context=context, extra_rows=extra_rows)


def _build_sppm_child_slots(*, nodes: list[dict[str, Any]], parent_series_id: str) -> list[PublicationArtifactSlot]:
    slots: list[PublicationArtifactSlot] = []
    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "").strip().lower()
        if kind != "subprocess":
            continue
        metadata = node.get("metadata")
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        detail_map_ref = resolve_subprocess_detail_map_reference(node_id=node_id, metadata=metadata_dict)
        slots.append(
            PublicationArtifactSlot(
                slot_id=f"child:{node_id}",
                title=normalize_space(str(node.get("name") or node_id)),
                kind="child_map",
                parent_series_id=parent_series_id,
                source_node_id=node_id,
                metadata={"detail_map_ref": detail_map_ref},
            )
        )
    return slots


def _build_sppm_footer_content(*, context: Any, options: RenderOptions) -> PublicationBandContent | None:
    metric_rows = [
        *_footer_metric_rows_from_metadata(context.metadata),
        *[(label, value) for label, value in options.sppm_footer_metrics],
    ]
    notes = [
        *_footer_notes_from_metadata(context.metadata),
        *[normalize_space(note) for note in options.sppm_footer_notes if normalize_space(note)],
    ]
    if not metric_rows and not notes:
        return None
    return PublicationBandContent(rows=tuple(metric_rows), notes=tuple(notes))


def _footer_metric_rows_from_metadata(metadata: dict[str, Any]) -> list[tuple[str, str]]:
    raw_metrics = (
        metadata.get("publication_footer_metrics")
        or metadata.get("footer_metrics")
        or metadata.get("analytics_footer_metrics")
        or metadata.get("analytics_metrics")
    )
    if isinstance(raw_metrics, dict):
        return _footer_metric_rows_from_mapping(raw_metrics)
    if isinstance(raw_metrics, (list, tuple)):
        return _footer_metric_rows_from_sequence(raw_metrics)
    return []


def _footer_metric_rows_from_mapping(raw_metrics: dict[Any, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for label, value in raw_metrics.items():
        row = _footer_metric_row(label=label, value=value)
        if row is not None:
            rows.append(row)
    return rows


def _footer_metric_rows_from_sequence(raw_metrics: list[Any] | tuple[Any, ...]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for item in raw_metrics:
        row = _footer_metric_row_from_item(item)
        if row is not None:
            rows.append(row)
    return rows


def _footer_metric_row_from_item(item: Any) -> tuple[str, str] | None:
    if isinstance(item, dict):
        return _footer_metric_row(label=item.get("label"), value=item.get("value"))
    if isinstance(item, (list, tuple)) and len(item) == 2:
        return _footer_metric_row(label=item[0], value=item[1])
    return None


def _footer_metric_row(*, label: Any, value: Any) -> tuple[str, str] | None:
    label_text = normalize_space(str(label or ""))
    value_text = normalize_space(str(value or ""))
    if not label_text or not value_text:
        return None
    return (label_text, value_text)


def _footer_notes_from_metadata(metadata: dict[str, Any]) -> list[str]:
    raw_notes = (
        metadata.get("publication_footer_notes")
        or metadata.get("footer_notes")
        or metadata.get("publication_footer")
        or metadata.get("footer_note")
    )
    if isinstance(raw_notes, str):
        note = normalize_space(raw_notes)
        return [note] if note else []
    if isinstance(raw_notes, (list, tuple)):
        return [normalize_space(str(note)) for note in raw_notes if normalize_space(str(note))]
    return []