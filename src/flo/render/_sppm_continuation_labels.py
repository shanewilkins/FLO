"""Continuation label helpers for SPPM publication output."""

from __future__ import annotations

import re
from typing import Any

from flo.schema.render_metadata import (
    SPPM_CONTINUATION_INCOMING_METADATA_KEYS,
    SPPM_CONTINUATION_OUTGOING_METADATA_KEYS,
    first_present_metadata_value,
)

from ._autoformat_wrap import WrapPlan
from ._continuation_labels import (
    build_continuation_label_attrs,
    format_continuation_html_label,
)
from ._sppm_step_refs import format_sppm_step_reference


def build_sppm_continuation_label_attrs(
    *,
    source: str,
    target: str,
    wrap_plan: WrapPlan,
    is_secondary: bool,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return outgoing and incoming continuation label attrs for a wrapped edge."""
    return build_continuation_label_attrs(
        source=source,
        target=target,
        wrap_plan=wrap_plan,
        is_secondary=is_secondary,
        reference_formatter=format_sppm_step_reference,
    )


def format_sppm_continuation_html_label(*, text: str, is_secondary: bool) -> str:
    """Return styled HTML-like Graphviz label markup for an SPPM continuation."""
    return format_continuation_html_label(text=text, is_secondary=is_secondary)


def build_sppm_continuation_anchor_tokens(
    *,
    source: str,
    target: str,
    wrap_plan: WrapPlan,
) -> tuple[str | None, str | None]:
    """Return outgoing/incoming continuation token labels for circular anchor markers."""
    if not wrap_plan.active or (source, target) not in wrap_plan.boundary_edges:
        return None, None

    source_chunk = wrap_plan.node_chunk_index.get(source)
    target_chunk = wrap_plan.node_chunk_index.get(target)
    if source_chunk is None or target_chunk is None or source_chunk == target_chunk:
        return None, None

    source_page = source_chunk + 1
    target_page = target_chunk + 1
    outgoing = (
        f"P{target_page}-{_continuation_suffix(format_sppm_step_reference(target))}"
    )
    incoming = (
        f"P{source_page}-{_continuation_suffix(format_sppm_step_reference(source))}"
    )
    return outgoing, incoming


def resolve_sppm_continuation_anchor_tokens(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    wrap_plan: WrapPlan,
) -> tuple[str | None, str | None]:
    """Return continuation tokens using explicit metadata aliases with wrap fallback."""
    metadata_obj = edge.get("metadata")
    metadata: dict[str, Any] = metadata_obj if isinstance(metadata_obj, dict) else {}
    outgoing = _normalize_continuation_token(
        first_present_metadata_value(metadata, SPPM_CONTINUATION_OUTGOING_METADATA_KEYS)
    )
    incoming = _normalize_continuation_token(
        first_present_metadata_value(metadata, SPPM_CONTINUATION_INCOMING_METADATA_KEYS)
    )

    if outgoing is None or incoming is None:
        derived_outgoing, derived_incoming = build_sppm_continuation_anchor_tokens(
            source=source,
            target=target,
            wrap_plan=wrap_plan,
        )
        if outgoing is None:
            outgoing = derived_outgoing
        if incoming is None:
            incoming = derived_incoming

    # For explicit single-sided tokens, mirror into the opposite marker so the
    # continuation remains visually explicit at both ends.
    if outgoing is None and incoming is not None:
        outgoing = incoming
    if incoming is None and outgoing is not None:
        incoming = outgoing
    return outgoing, incoming


def build_sppm_continuation_anchor_attrs(
    *, token: str, is_secondary: bool
) -> tuple[str, ...]:
    """Return DOT node attrs for a circular continuation anchor marker."""
    border = "#90A4AE" if is_secondary else "#455A64"
    fill = "#ECEFF1" if is_secondary else "#FFFFFF"
    fontsize = "8" if is_secondary else "9"
    return (
        "shape=circle",
        "width=0.58",
        "height=0.58",
        "fixedsize=true",
        "style=filled",
        f'fillcolor="{fill}"',
        f'color="{border}"',
        "penwidth=1.2",
        "fontname=Helvetica",
        f"fontsize={fontsize}",
        f'label="{token}"',
    )


def _continuation_suffix(reference: str) -> str:
    """Return the first alphanumeric marker from a step reference (e.g. ``[queue]`` -> ``Q``)."""
    normalized = reference.strip().strip("[]")
    match = re.search(r"[A-Za-z0-9]", normalized)
    if match is None:
        return "X"
    return match.group(0).upper()


def _normalize_continuation_token(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized
