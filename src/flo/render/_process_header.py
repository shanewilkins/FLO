"""Shared process-header extraction helpers for renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.schema.render_metadata import (
    PROCESS_HEADER_METADATA_FIELDS,
    PROCESS_METADATA_PROCESS_ID_KEY,
    PROCESS_METADATA_PROCESS_NAME_KEY,
)

from ._sppm_text import normalize_space

DEFAULT_PROCESS_HEADER_METADATA_FIELDS = PROCESS_HEADER_METADATA_FIELDS


@dataclass(frozen=True)
class ProcessHeaderContext:
    """Renderer-agnostic process title/header data."""

    title: str
    metadata: dict[str, Any]


def extract_process_header_context(process: Any) -> ProcessHeaderContext:
    """Return normalized process title and metadata for renderer header bands."""
    if isinstance(process, dict):
        return _extract_dict_header_context(process)
    return _extract_ir_header_context(process)


def _extract_dict_header_context(process: dict[str, Any]) -> ProcessHeaderContext:
    process_dict = _as_string_key_dict(process.get("process"))
    metadata = _as_string_key_dict(process_dict.get("metadata"))
    _set_metadata_if_present(metadata, PROCESS_METADATA_PROCESS_ID_KEY, process_dict.get("id"))
    _set_metadata_if_present(metadata, PROCESS_METADATA_PROCESS_NAME_KEY, process_dict.get("name"))
    title = _first_nonempty_text(process_dict.get("name"), process_dict.get("id"), process.get("name"))
    return ProcessHeaderContext(title=normalize_space(title), metadata=metadata)


def _extract_ir_header_context(process: Any) -> ProcessHeaderContext:
    metadata = _as_string_key_dict(getattr(process, "process_metadata", None))
    title = _first_nonempty_text(
        metadata.get(PROCESS_METADATA_PROCESS_NAME_KEY),
        getattr(process, "name", None),
        metadata.get(PROCESS_METADATA_PROCESS_ID_KEY),
    )
    return ProcessHeaderContext(title=normalize_space(title), metadata=metadata)


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
    metadata_fields: tuple[tuple[str, str], ...] = DEFAULT_PROCESS_HEADER_METADATA_FIELDS,
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
    if extra_rows:
        rows.extend((label, normalize_space(value)) for label, value in extra_rows if value and normalize_space(value))
    return rows