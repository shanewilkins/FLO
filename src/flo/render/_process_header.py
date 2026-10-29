"""Shared process-header extraction helpers for renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.process.analysis.timing import analyze_process_timing
from flo.process.durations import duration_seconds
from flo.process.ir.models import IR
from flo.process.measurements import selected_result
from flo.process.schema.render_metadata import (
    PROCESS_HEADER_METADATA_FIELDS,
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
    PUBLICATION_EXTENSION_KEY,
)

from ._text import normalize_space

DEFAULT_PROCESS_HEADER_METADATA_FIELDS = PROCESS_HEADER_METADATA_FIELDS


@dataclass(frozen=True)
class ProcessHeaderContext:
    """Renderer-agnostic process title/header data."""

    title: str
    metadata: dict[str, Any]
    evidence_rows: tuple[tuple[str, str], ...] = ()


def extract_process_header_context(process: Any) -> ProcessHeaderContext:
    """Return normalized process title and metadata for renderer header bands."""
    if isinstance(process, dict):
        return _extract_dict_header_context(process)
    return _extract_ir_header_context(process)


def _extract_dict_header_context(process: dict[str, Any]) -> ProcessHeaderContext:
    process_dict = _as_string_key_dict(process.get("process"))
    metadata = _publication_annotations(process_dict.get("extensions"))
    _add_context_fields(
        metadata, process_dict.get("owner"), process_dict.get("version")
    )
    _set_metadata_if_present(
        metadata, PROCESS_METADATA_PROCESS_ID_KEY, process_dict.get("id")
    )
    _set_metadata_if_present(
        metadata, PROCESS_METADATA_PROCESS_NAME_KEY, process_dict.get("name")
    )
    title = _first_nonempty_text(
        process_dict.get("name"), process_dict.get("id"), process.get("name")
    )
    return ProcessHeaderContext(
        title=normalize_space(title),
        metadata=metadata,
        evidence_rows=process_evidence_rows(process),
    )


def _extract_ir_header_context(process: Any) -> ProcessHeaderContext:
    identity = _as_string_key_dict(getattr(process, "process_metadata", None))
    metadata = _publication_annotations(getattr(process, "extensions", None))
    for key in (PROCESS_METADATA_PROCESS_ID_KEY, PROCESS_METADATA_PROCESS_NAME_KEY):
        if key in identity:
            metadata[key] = identity[key]
    _add_context_fields(
        metadata,
        getattr(process, "process_owner", None),
        getattr(process, "process_version", None),
    )
    title = _first_nonempty_text(
        metadata.get(PROCESS_METADATA_PROCESS_NAME_KEY),
        getattr(process, "name", None),
        metadata.get(PROCESS_METADATA_PROCESS_ID_KEY),
    )
    return ProcessHeaderContext(
        title=normalize_space(title),
        metadata=metadata,
        evidence_rows=process_evidence_rows(process),
    )


def _publication_annotations(extensions: Any) -> dict[str, Any]:
    if not isinstance(extensions, dict):
        return {}
    return _as_string_key_dict(extensions.get(PUBLICATION_EXTENSION_KEY))


def _add_context_fields(metadata: dict[str, Any], owner: Any, version: Any) -> None:
    if isinstance(owner, dict) and owner.get("name"):
        metadata["owner"] = owner["name"]
    if version is not None:
        metadata["revision"] = str(version)


def _as_string_key_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _set_metadata_if_present(metadata: dict[str, Any], key: str, value: Any) -> None:
    text = _nonempty_text(value)
    if text:
        metadata.setdefault(key, text)


def _first_nonempty_text(*values: Any) -> str:
    for value in values:
        text = _nonempty_text(value)
        if text:
            return text
    return ""


def _nonempty_text(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def build_process_header_rows(
    *,
    context: ProcessHeaderContext,
    metadata_fields: tuple[
        tuple[str, str], ...
    ] = DEFAULT_PROCESS_HEADER_METADATA_FIELDS,
    extra_rows: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """Return display-ready header rows for a renderer-specific header band."""
    rows: list[tuple[str, str]] = []
    for key, label in metadata_fields:
        value = context.metadata.get(key)
        if isinstance(value, str) and value.strip():
            normalized = normalize_space(value)
            if key == PROCESS_METADATA_PROCESS_ID_KEY and normalized == context.title:
                continue
            rows.append((label, normalized))
    rows.extend(context.evidence_rows)
    if extra_rows:
        rows.extend(
            (label, normalize_space(value))
            for label, value in extra_rows
            if value and normalize_space(value)
        )
    return rows


def process_evidence_rows(process: Any) -> tuple[tuple[str, str], ...]:
    """Present supplied evidence separately from modeled totals and relations."""
    if not isinstance(process, IR):
        return ()
    rows: list[tuple[str, str]] = []
    if process.lead_time is not None:
        profile = process.lead_time
        result = selected_result(profile, "primary")
        seconds = duration_seconds(result)
        rows.append(
            (
                f"Supplied lead time ({profile.get('basis')})",
                "?" if seconds is None else f"{seconds / 60:g} min",
            )
        )
        analysis = analyze_process_timing(process)
        modeled = analysis.modeled_lead_time_seconds
        minimum = analysis.minimum_path_lead_time_seconds
        maximum = analysis.maximum_path_lead_time_seconds
        if modeled is not None:
            rows.append(("Modeled lead time", f"{modeled / 60:g} min"))
        elif minimum is not None and maximum is not None:
            rows.append(
                ("Modeled lead time range", f"{minimum / 60:g} to {maximum / 60:g} min")
            )
        else:
            rows.append(("Modeled lead time", "not derivable"))
    for edge in process.edges:
        if isinstance(edge.handoff, dict):
            rows.append(
                (
                    f"Handoff {edge.source} → {edge.target}",
                    edge.handoff.get("type") or "unspecified",
                )
            )
        if isinstance(edge.rework, dict):
            relation = edge.rework
            value = relation.get("reason") or "unspecified"
            frequency = relation.get("frequency")
            if isinstance(frequency, dict):
                value += f"; {frequency['numerator']:g} of {frequency['denominator']:g} {frequency['observation_unit']} ({frequency['basis']})"
                if frequency.get("evidence_ref"):
                    value += f"; evidence: {frequency['evidence_ref']}"
            if relation.get("note"):
                value += f"; note: {relation['note']}"
            rows.append((f"Rework {edge.source} → {edge.target}", value))
    return tuple(rows)
