"""Support helpers for SPPM publication plan shaping."""

from __future__ import annotations

from typing import Any

from flo.schema.render_metadata import (
    SPPM_FOOTER_METRIC_METADATA_KEYS,
    SPPM_FOOTER_NOTES_METADATA_KEYS,
    first_present_metadata_value,
)
from flo.schema.subprocess_refs import resolve_subprocess_detail_map_reference

from ._process_header import build_process_header_rows
from ._publication import PublicationArtifactSlot, PublicationBandContent
from ._sppm_projection import SppmProjectionContext
from ._sppm_text import normalize_space
from .options import RenderOptions


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
    raw_metrics = first_present_metadata_value(metadata, SPPM_FOOTER_METRIC_METADATA_KEYS)
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
    raw_notes = first_present_metadata_value(metadata, SPPM_FOOTER_NOTES_METADATA_KEYS)
    if isinstance(raw_notes, str):
        note = normalize_space(raw_notes)
        return [note] if note else []
    if isinstance(raw_notes, (list, tuple)):
        return [normalize_space(str(note)) for note in raw_notes if normalize_space(str(note))]
    return []