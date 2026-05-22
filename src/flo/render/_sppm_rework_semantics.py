"""Dependency-light helpers for backend-neutral SPPM rework edge semantics."""

from __future__ import annotations

from typing import Any, Literal

SppmReworkVariant = Literal["branch", "return"]


def is_sppm_rework_edge(edge: dict[str, Any]) -> bool:
    """Return True when edge explicitly represents SPPM rework semantics."""
    edge_type = str(edge.get("edge_type") or "").strip().lower()
    if edge_type == "rework":
        return True
    return bool(edge.get("rework"))


def is_explicit_rework_branch_out(*, edge: dict[str, Any], source_kind: str) -> bool:
    """Return True when edge represents outbound rework from a decision context."""
    if not is_sppm_rework_edge(edge):
        return False
    return (
        source_kind == "decision"
        or edge.get("outcome") is not None
        or edge.get("label") is not None
    )


def resolve_sppm_rework_variant(
    edge: dict[str, Any], *, source_kind: str
) -> SppmReworkVariant | None:
    """Return the semantic rework variant for an edge when it is explicit."""
    if not is_sppm_rework_edge(edge):
        return None
    if is_explicit_rework_branch_out(edge=edge, source_kind=source_kind):
        return "branch"
    return "return"
