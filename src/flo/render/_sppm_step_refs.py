"""Stable visible step reference helpers for SPPM publication output."""

from __future__ import annotations


def format_sppm_step_reference(node_id: str) -> str:
    """Return the visible stable reference token for an SPPM node."""
    return f"[{node_id.strip()}]"