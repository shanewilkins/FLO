"""Shared renderer-facing metadata contracts.

This module centralizes metadata keys and alias chains used by render and
compile surfaces so key conventions stay discoverable and consistent.
"""

from __future__ import annotations

from typing import Any

from .subprocess_refs import SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS

PROCESS_METADATA_PROCESS_ID_KEY = "process_id"
PROCESS_METADATA_PROCESS_NAME_KEY = "process_name"
PROCESS_METADATA_OWNER_KEY = "owner"
PROCESS_METADATA_REVISION_KEY = "revision"
PROCESS_METADATA_PUBLICATION_DATE_KEY = "publication_date"

PROCESS_HEADER_METADATA_FIELDS: tuple[tuple[str, str], ...] = (
    (PROCESS_METADATA_PROCESS_ID_KEY, "Process"),
    (PROCESS_METADATA_OWNER_KEY, "Owner"),
    (PROCESS_METADATA_REVISION_KEY, "Revision"),
    (PROCESS_METADATA_PUBLICATION_DATE_KEY, "Date"),
)

SPPM_FOOTER_METRIC_METADATA_KEYS: tuple[str, ...] = (
    "publication_legend_items",
    "legend_items",
    "legend",
    "publication_footer_metrics",
    "footer_metrics",
    "analytics_footer_metrics",
    "analytics_metrics",
)

SPPM_FOOTER_NOTES_METADATA_KEYS: tuple[str, ...] = (
    "publication_caption",
    "caption",
    "publication_footer_notes",
    "footer_notes",
    "publication_footer",
    "footer_note",
)

SPPM_CONTINUATION_OUTGOING_METADATA_KEYS: tuple[str, ...] = (
    "continuation_to",
    "continuation_out",
    "continuation_token_out",
)

SPPM_CONTINUATION_INCOMING_METADATA_KEYS: tuple[str, ...] = (
    "continuation_from",
    "continuation_in",
    "continuation_token_in",
)


def first_present_metadata_value(
    metadata: dict[str, Any], candidate_keys: tuple[str, ...]
) -> Any:
    """Return the first truthy metadata value for a candidate key list."""
    for key in candidate_keys:
        value = metadata.get(key)
        if value:
            return value
    return None


__all__ = [
    "PROCESS_HEADER_METADATA_FIELDS",
    "PROCESS_METADATA_PROCESS_ID_KEY",
    "PROCESS_METADATA_PROCESS_NAME_KEY",
    "SPPM_CONTINUATION_INCOMING_METADATA_KEYS",
    "SPPM_CONTINUATION_OUTGOING_METADATA_KEYS",
    "SPPM_FOOTER_METRIC_METADATA_KEYS",
    "SPPM_FOOTER_NOTES_METADATA_KEYS",
    "SUBPROCESS_DETAIL_MAP_REFERENCE_KEYS",
    "first_present_metadata_value",
]
