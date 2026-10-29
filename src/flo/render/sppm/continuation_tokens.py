"""Dependency-light helpers for explicit SPPM continuation tokens."""

from __future__ import annotations

from typing import Any

from flo.process.schema.render_metadata import CONTINUATION_EXTENSION_KEY


def resolve_explicit_sppm_continuation_tokens(
    edge: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Return mirrored continuation tokens using explicit edge metadata only."""
    extensions = edge.get("extensions") or {}
    tokens = extensions.get(CONTINUATION_EXTENSION_KEY) or {}
    outgoing = _normalize_continuation_token(tokens.get("outgoing"))
    incoming = _normalize_continuation_token(tokens.get("incoming"))
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
