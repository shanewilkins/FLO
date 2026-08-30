"""Support helpers for SPPM publication plan shaping."""

from __future__ import annotations

from typing import Any

from flo.process.analysis import ProcessTimingAnalysis
from flo.process.schema.render_metadata import (
    SPPM_FOOTER_METRIC_METADATA_KEYS,
    SPPM_FOOTER_NOTES_METADATA_KEYS,
    first_present_metadata_value,
)
from flo.process.schema.subprocess_refs import resolve_subprocess_detail_map_reference
from flo.errors import RenderError

from .._process_header import build_process_header_rows
from .._publication import (
    PublicationArtifactSlot,
    PublicationBandContent,
    PublicationBounds,
    PublicationDiagnostic,
    PublicationMargins,
    build_publication_canvas,
    build_publication_canvas_for_format,
    evaluate_publication_fallback,
)
from .projection import SppmProjectionContext
from .text import format_text_field, normalize_space
from ..options import RenderOptions

_DEFAULT_SPPM_PUBLICATION_WIDTH_PX = 1200
_DEFAULT_SPPM_PUBLICATION_MARGINS = PublicationMargins(
    top_px=48, right_px=48, bottom_px=48, left_px=48
)
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
    if (
        projection.effective_mode == "top_level"
        and options.subprocess_view == "parent_only"
    ):
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
        extra_rows.append(
            ("Projection Fallback", projection.fallback_reason.replace("-", " "))
        )
    for diagnostic in diagnostics:
        if diagnostic.severity == "warning":
            extra_rows.append(("Readability Warning", diagnostic.message))
    extra_rows.append(("Nodes", str(len(nodes))))
    extra_rows.append(("Edges", str(len(edges))))
    extra_rows = [
        (
            _format_sppm_publication_text(
                label, options=options, max_len=options.sppm_max_label_step_name
            ),
            _format_sppm_publication_text(
                value, options=options, max_len=options.sppm_max_label_step_name
            ),
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
        detail_map_ref = resolve_subprocess_detail_map_reference(
            node_id=node_id, metadata=metadata_dict
        )
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


def _build_sppm_footer_content(
    *,
    context: Any,
    options: RenderOptions,
    nodes: list[dict[str, Any]] | None = None,
    timing_analysis: ProcessTimingAnalysis | None = None,
) -> PublicationBandContent | None:
    timing_rows, timing_notes = _footer_content_from_timing_analysis(
        timing_analysis,
        visible_nodes=nodes or [],
        options=options,
    )
    metric_rows = _merge_footer_metric_rows(
        [
            *timing_rows,
            *_footer_metric_rows_from_metadata(context.metadata, options=options),
            *[
                _footer_metric_row(label=label, value=value, options=options)
                for label, value in options.sppm_footer_metrics
            ],
        ]
    )
    notes = [
        *timing_notes,
        *_footer_notes_from_metadata(context.metadata, options=options),
        *[
            _format_sppm_publication_text(
                note, options=options, max_len=options.sppm_max_label_step_name
            )
            for note in options.sppm_footer_notes
            if normalize_space(note)
        ],
    ]
    notes = [note for note in notes if note]
    if not metric_rows and not notes:
        return None
    return PublicationBandContent(rows=tuple(metric_rows), notes=tuple(notes))


def _footer_content_from_timing_analysis(
    analysis: ProcessTimingAnalysis | None,
    *,
    visible_nodes: list[dict[str, Any]],
    options: RenderOptions,
) -> tuple[list[tuple[str, str]], list[str]]:
    if analysis is None or not _analysis_matches_visible_process(
        analysis, visible_nodes=visible_nodes
    ):
        return [], []
    missing_ids = set(analysis.missing_timing_node_ids)
    has_declared_timing = any(
        (
            timing.node_type in {"task", "system_task", "subprocess", "queue"}
            and timing.node_id not in missing_ids
        )
        or timing.changeover_source_field is not None
        for timing in analysis.node_timings
    )
    if not has_declared_timing:
        return [], []

    totals = analysis.declared_totals
    raw_rows: list[tuple[str, str]] = [
        ("Cycle Time", _format_timing_seconds(totals.cycle_time_seconds)),
        ("Waiting Time", _format_timing_seconds(totals.wait_time_seconds)),
        ("C/O Time", _format_timing_seconds(totals.changeover_time_seconds)),
    ]
    if analysis.modeled_lead_time_seconds is not None:
        raw_rows.append(
            ("Lead Time", _format_timing_seconds(analysis.modeled_lead_time_seconds))
        )
    elif (
        analysis.minimum_path_lead_time_seconds is not None
        and analysis.maximum_path_lead_time_seconds is not None
    ):
        raw_rows.append(
            (
                "Lead Time Range",
                f"{_format_timing_seconds(analysis.minimum_path_lead_time_seconds)} "
                f"to {_format_timing_seconds(analysis.maximum_path_lead_time_seconds)}",
            )
        )
    else:
        raw_rows.append(("Lead Time", "Unavailable"))

    rows = [
        row
        for label, value in raw_rows
        if (row := _footer_metric_row(label=label, value=value, options=options))
        is not None
    ]
    notes: list[str] = []
    if analysis.diagnostics:
        note = _format_sppm_publication_text(
            "Timing diagnostics available; run flo inspect for details.",
            options=options,
            max_len=options.sppm_max_label_step_name,
        )
        if note:
            notes.append(note)
    return rows, notes


def _analysis_matches_visible_process(
    analysis: ProcessTimingAnalysis,
    *,
    visible_nodes: list[dict[str, Any]],
) -> bool:
    analyzed_ids = {timing.node_id for timing in analysis.node_timings}
    visible_ids = {
        str(node.get("id") or "").strip()
        for node in visible_nodes
        if str(node.get("id") or "").strip()
    }
    return bool(analyzed_ids) and visible_ids == analyzed_ids


def _format_timing_seconds(seconds: float) -> str:
    if seconds == 0:
        return "0 min"
    if seconds % 60 == 0:
        return f"{_format_timing_number(seconds / 60)} min"
    return f"{_format_timing_number(seconds)} s"


def _format_timing_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _merge_footer_metric_rows(
    rows: list[tuple[str, str] | None],
) -> list[tuple[str, str]]:
    """Allow later explicit rows to replace generated defaults by label."""
    merged: list[tuple[str, str]] = []
    index_by_label: dict[str, int] = {}
    for row in rows:
        if row is None:
            continue
        label_key = normalize_space(row[0]).casefold()
        existing_index = index_by_label.get(label_key)
        if existing_index is None:
            index_by_label[label_key] = len(merged)
            merged.append(row)
        else:
            merged[existing_index] = row
    return merged


def _footer_metric_rows_from_metadata(
    metadata: dict[str, Any], *, options: RenderOptions
) -> list[tuple[str, str]]:
    raw_metrics = first_present_metadata_value(
        metadata, SPPM_FOOTER_METRIC_METADATA_KEYS
    )
    if isinstance(raw_metrics, dict):
        return _footer_metric_rows_from_mapping(raw_metrics, options=options)
    if isinstance(raw_metrics, (list, tuple)):
        return _footer_metric_rows_from_sequence(raw_metrics, options=options)
    return []


def _footer_metric_rows_from_mapping(
    raw_metrics: dict[Any, Any], *, options: RenderOptions
) -> list[tuple[str, str]]:
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


def _footer_metric_row_from_item(
    item: Any, *, options: RenderOptions
) -> tuple[str, str] | None:
    if isinstance(item, dict):
        return _footer_metric_row(
            label=item.get("label"), value=item.get("value"), options=options
        )
    if isinstance(item, (list, tuple)) and len(item) == 2:
        return _footer_metric_row(label=item[0], value=item[1], options=options)
    return None


def _footer_metric_row(
    *, label: Any, value: Any, options: RenderOptions
) -> tuple[str, str] | None:
    label_text = _format_sppm_publication_text(
        label, options=options, max_len=options.sppm_max_label_step_name
    )
    value_text = _format_sppm_publication_text(
        value, options=options, max_len=options.sppm_max_label_ctwt
    )
    if not label_text or not value_text:
        return None
    return (label_text, value_text)


def _footer_notes_from_metadata(
    metadata: dict[str, Any], *, options: RenderOptions
) -> list[str]:
    raw_notes = first_present_metadata_value(metadata, SPPM_FOOTER_NOTES_METADATA_KEYS)
    if isinstance(raw_notes, str):
        note = _format_sppm_publication_text(
            raw_notes, options=options, max_len=options.sppm_max_label_step_name
        )
        return [note] if note else []
    if isinstance(raw_notes, (list, tuple)):
        return [
            _format_sppm_publication_text(
                note, options=options, max_len=options.sppm_max_label_step_name
            )
            for note in raw_notes
            if normalize_space(str(note))
        ]
    return []


def _format_sppm_publication_text(
    value: Any, *, options: RenderOptions, max_len: int | None
) -> str:
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
    header_rows: list[tuple[str, str]],
    footer_content: PublicationBandContent | None,
    options: RenderOptions,
    show_header: bool,
) -> Any:
    header_height_px = (
        _publication_band_height(
            title=title,
            row_count=len(header_rows),
            note_count=0,
            minimum_height_px=_SPPM_HEADER_BAND_HEIGHT_PX,
            scale=options.resolved_theme.typography_scale,
        )
        if (show_header and title)
        else 0
    )
    footer_height_px = (
        _publication_band_height(
            title="",
            row_count=len(footer_content.rows) if footer_content else 0,
            note_count=len(footer_content.notes) if footer_content else 0,
            minimum_height_px=72,
            scale=options.resolved_theme.typography_scale,
        )
        if footer_content is not None
        else 0
    )
    if options.publication_page_format:
        return build_publication_canvas_for_format(
            page_format=options.publication_page_format,
            header_height_px=header_height_px,
            footer_height_px=footer_height_px,
            width_px_override=options.layout_max_width_px,
        )
    return build_publication_canvas(
        bounds=PublicationBounds(
            width_px=options.layout_max_width_px or _DEFAULT_SPPM_PUBLICATION_WIDTH_PX
        ),
        margins=_DEFAULT_SPPM_PUBLICATION_MARGINS,
        header_height_px=header_height_px,
        footer_height_px=footer_height_px,
    )


def _publication_band_height(
    *,
    title: str,
    row_count: int,
    note_count: int,
    minimum_height_px: int,
    scale: float = 1.0,
) -> int:
    content_height = 24 if title else 0
    content_height += (row_count + note_count) * 16
    return int(round(max(minimum_height_px, content_height + 32) * scale))


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


def _raise_for_publication_errors(
    diagnostics: tuple[PublicationDiagnostic, ...],
) -> None:
    errors = [
        diagnostic.message
        for diagnostic in diagnostics
        if diagnostic.severity == "error"
    ]
    if errors:
        raise RenderError("; ".join(errors))


def _serialize_diagnostics(
    diagnostics: tuple[PublicationDiagnostic, ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "code": diagnostic.code,
            "severity": diagnostic.severity,
            "message": diagnostic.message,
            **diagnostic.metadata,
        }
        for diagnostic in diagnostics
    )
