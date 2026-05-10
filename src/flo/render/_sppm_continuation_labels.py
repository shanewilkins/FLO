"""Continuation label helpers for SPPM publication output."""

from __future__ import annotations

from ._autoformat_wrap import WrapPlan
from ._continuation_labels import build_continuation_label_attrs, format_continuation_html_label
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