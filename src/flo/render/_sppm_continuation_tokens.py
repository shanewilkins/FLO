"""Dependency-light helpers for explicit SPPM continuation tokens."""

from __future__ import annotations

from typing import Any

from flo.schema.render_metadata import (
    SPPM_CONTINUATION_INCOMING_METADATA_KEYS,
    SPPM_CONTINUATION_OUTGOING_METADATA_KEYS,
    first_present_metadata_value,
)


def resolve_explicit_sppm_continuation_tokens(
    edge: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Return mirrored continuation tokens using explicit edge metadata only."""
    metadata_obj = edge.get("metadata")
    metadata: dict[str, Any] = metadata_obj if isinstance(metadata_obj, dict) else {}
    outgoing = _normalize_continuation_token(
        first_present_metadata_value(metadata, SPPM_CONTINUATION_OUTGOING_METADATA_KEYS)
    )
    incoming = _normalize_continuation_token(
        first_present_metadata_value(metadata, SPPM_CONTINUATION_INCOMING_METADATA_KEYS)
    )
    if outgoing is None and incoming is not None:
        outgoing = incoming
    if incoming is None and outgoing is not None:
        incoming = outgoing
    return outgoing, incoming


def _normalize_continuation_token(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized
