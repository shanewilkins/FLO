"""Support helpers for SPPM publication plan shaping."""

from __future__ import annotations

from typing import Any

from flo.schema.render_metadata import (
    SPPM_FOOTER_METRIC_METADATA_KEYS,
    SPPM_FOOTER_NOTES_METADATA_KEYS,
    first_present_metadata_value,
)
from flo.schema.subprocess_refs import resolve_subprocess_detail_map_reference
from flo.services.errors import RenderError

from ._process_header import build_process_header_rows
from ._publication import (
    PublicationArtifactSlot,
    PublicationBandContent,
    PublicationBounds,
    PublicationDiagnostic,
    PublicationMargins,
    build_publication_canvas,
    build_publication_canvas_for_format,
    evaluate_publication_fallback,
)
from ._sppm_metadata_schema import (
    get_metadata_wait_time_minutes,
    get_metadata_crossover_time,
)
from ._sppm_projection import SppmProjectionContext
from ._sppm_text import format_text_field, normalize_space
from .options import RenderOptions

_DEFAULT_SPPM_PUBLICATION_WIDTH_PX = 1200
_DEFAULT_SPPM_PUBLICATION_MARGINS = PublicationMargins(top_px=48, right_px=48, bottom_px=48, left_px=48)
_SPPM_HEADER_BAND_HEIGHT_PX = 96


def _build_sppm_header_rows(
    *,
    context: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    projection: SppmProjectionContext,
    diagnostics: tuple[Any, ...],
) -> list[tuple[str, str]]:
    extra_rows: list[tuple[str, str]] = []
    if options.sppm_output_profile != "default":
        extra_rows.append(("Profile", options.sppm_output_profile))
    if projection.effective_mode == "top_level" and options.subprocess_view == "parent_only":
        extra_rows.append(("Subprocess View", "parent-only"))
    if projection.effective_mode != "top_level":
        extra_rows.append(("Projection", projection.effective_mode.replace("_", "-")))
    if projection.focus_subprocess:
        extra_rows.append(("Focus", projection.focus_subprocess))
    if projection.parent_subprocess:
        extra_rows.append(("Parent", projection.parent_subprocess))
    if projection.entry_context:
        extra_rows.append(("Entry Context", ", ".join(projection.entry_context)))
    if projection.exit_context:
        extra_rows.append(("Exit Context", ", ".join(projection.exit_context)))
    if projection.fallback_reason:
        extra_rows.append(("Projection Fallback", projection.fallback_reason.replace("-", " ")))
    for diagnostic in diagnostics:
        if diagnostic.severity == "warning":
            extra_rows.append(("Readability Warning", diagnostic.message))
    extra_rows.append(("Nodes", str(len(nodes))))
    extra_rows.append(("Edges", str(len(edges))))
    extra_rows = [
        (
            _format_sppm_publication_text(label, options=options, max_len=options.sppm_max_label_step_name),
            _format_sppm_publication_text(value, options=options, max_len=options.sppm_max_label_step_name),
        )
        for label, value in extra_rows
    ]
    return build_process_header_rows(context=context, extra_rows=extra_rows)


def _build_sppm_child_slots(
    *,
    nodes: list[dict[str, Any]],
    parent_series_id: str,
    focus_subprocess: str | None,
) -> list[PublicationArtifactSlot]:
    slots: list[PublicationArtifactSlot] = []
    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            continue
        if focus_subprocess and node_id == focus_subprocess:
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


def _build_sppm_footer_content(*, context: Any, options: RenderOptions, nodes: list[dict[str, Any]] | None = None) -> PublicationBandContent | None:
    metric_rows = [
        *_footer_metric_rows_from_metadata(context.metadata, options=options),
        *_footer_metric_rows_from_node_aggregation(nodes=nodes or [], options=options),
        *[_footer_metric_row(label=label, value=value, options=options) for label, value in options.sppm_footer_metrics],
    ]
    metric_rows = [row for row in metric_rows if row is not None]
    notes = [
        *_footer_notes_from_metadata(context.metadata, options=options),
        *[
            _format_sppm_publication_text(note, options=options, max_len=options.sppm_max_label_step_name)
            for note in options.sppm_footer_notes
            if normalize_space(note)
        ],
    ]
    notes = [note for note in notes if note]
    if not metric_rows and not notes:
        return None
    return PublicationBandContent(rows=tuple(metric_rows), notes=tuple(notes))


def _footer_metric_rows_from_node_aggregation(
    *,
    nodes: list[dict[str, Any]],
    options: RenderOptions,
) -> list[tuple[str, str]]:
    """Auto-aggregate wait time and crossover time metrics from process nodes.
    
    Collects WT and CO values from all nodes and sums them for footer display.
    This helps visualize total process delays in a diagnostic way.
    """
    rows: list[tuple[str, str]] = []
    total_wt: float = 0.0
    total_co: float = 0.0
    
    for node in nodes:
        metadata = node.get("metadata") or {}
        if not isinstance(metadata, dict):
            continue
        
        wt_minutes = get_metadata_wait_time_minutes(metadata)
        if wt_minutes and wt_minutes > 0:
            total_wt += wt_minutes
        
        co_value = get_metadata_crossover_time(metadata)
        if co_value is not None and co_value.numeric_value > 0:
            total_co += co_value.numeric_value
    
    if total_wt > 0:
        wt_row = _footer_metric_row(
            label="Waiting Time",
            value=f"{int(total_wt) if total_wt == int(total_wt) else total_wt} min",
            options=options,
        )
        if wt_row is not None:
            rows.append(wt_row)
    
    if total_co > 0:
        co_row = _footer_metric_row(
            label="Changeover Time",
            value=f"{int(total_co) if total_co == int(total_co) else total_co} min",
            options=options,
        )
        if co_row is not None:
            rows.append(co_row)
    
    return rows


def _footer_metric_rows_from_metadata(metadata: dict[str, Any], *, options: RenderOptions) -> list[tuple[str, str]]:
    raw_metrics = first_present_metadata_value(metadata, SPPM_FOOTER_METRIC_METADATA_KEYS)
    if isinstance(raw_metrics, dict):
        return _footer_metric_rows_from_mapping(raw_metrics, options=options)
    if isinstance(raw_metrics, (list, tuple)):
        return _footer_metric_rows_from_sequence(raw_metrics, options=options)
    return []


def _footer_metric_rows_from_mapping(raw_metrics: dict[Any, Any], *, options: RenderOptions) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for label, value in raw_metrics.items():
        row = _footer_metric_row(label=label, value=value, options=options)
        if row is not None:
            rows.append(row)
    return rows


def _footer_metric_rows_from_sequence(
    raw_metrics: list[Any] | tuple[Any, ...],
    *,
    options: RenderOptions,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for item in raw_metrics:
        row = _footer_metric_row_from_item(item, options=options)
        if row is not None:
            rows.append(row)
    return rows


def _footer_metric_row_from_item(item: Any, *, options: RenderOptions) -> tuple[str, str] | None:
    if isinstance(item, dict):
        return _footer_metric_row(label=item.get("label"), value=item.get("value"), options=options)
    if isinstance(item, (list, tuple)) and len(item) == 2:
        return _footer_metric_row(label=item[0], value=item[1], options=options)
    return None


def _footer_metric_row(*, label: Any, value: Any, options: RenderOptions) -> tuple[str, str] | None:
    label_text = _format_sppm_publication_text(label, options=options, max_len=options.sppm_max_label_step_name)
    value_text = _format_sppm_publication_text(value, options=options, max_len=options.sppm_max_label_ctwt)
    if not label_text or not value_text:
        return None
    return (label_text, value_text)


def _footer_notes_from_metadata(metadata: dict[str, Any], *, options: RenderOptions) -> list[str]:
    raw_notes = first_present_metadata_value(metadata, SPPM_FOOTER_NOTES_METADATA_KEYS)
    if isinstance(raw_notes, str):
        note = _format_sppm_publication_text(raw_notes, options=options, max_len=options.sppm_max_label_step_name)
        return [note] if note else []
    if isinstance(raw_notes, (list, tuple)):
        return [
            _format_sppm_publication_text(note, options=options, max_len=options.sppm_max_label_step_name)
            for note in raw_notes
            if normalize_space(str(note))
        ]
    return []


def _format_sppm_publication_text(value: Any, *, options: RenderOptions, max_len: int | None) -> str:
    text = normalize_space(str(value or ""))
    if not text:
        return ""
    return format_text_field(
        text,
        max_len=max_len,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break=" ",
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