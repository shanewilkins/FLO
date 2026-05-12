"""SPPM SVG postprocess contract types.

Stable, renderer-owned data that tells the SVG postprocessor exactly which
edges to rewrite without relying on fragile DOT text or SVG title matching.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class SppmSvgPostprocessEdge:
    """One edge expected by the SVG postprocessor.

    Carries a stable logical ID and metadata so rewrite logic doesn't need
    to parse DOT or SVG text to discover what to rewrite.
    """

    edge_id: str
    source_id: str
    target_id: str
    edge_kind: str  # "wrap_boundary" | "rework_return" | "rework_branch"
    expected_segment_count: int
    anchor_id: str | None = None
    label_text: str | None = None


@dataclass(frozen=True)
class SppmSvgPostprocessContract:
    """Manifest of expected SVG edge rewrites for one SPPM diagram.

    Built by the routing layer and passed through to the SVG postprocessor,
    replacing regex-based DOT/SVG scanning with an explicit edge registry.
    """

    wrapped_boundary_edges: tuple[SppmSvgPostprocessEdge, ...] = ()
    rework_return_edges: tuple[SppmSvgPostprocessEdge, ...] = ()
    rework_branch_edges: tuple[SppmSvgPostprocessEdge, ...] = ()
    decision_outcome_label_edges: tuple[SppmSvgPostprocessEdge, ...] = ()


def _id_part(value: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in value) or "edge"


def _tailport_side(attrs: tuple[str, ...]) -> str | None:
    for attr in attrs:
        if not attr.startswith("tailport="):
            continue
        raw = attr.split("=", 1)[1].strip().strip('"')
        if ":" in raw:
            return raw.rsplit(":", 1)[1]
        return raw
    return None


def _xlabel_value(attrs: tuple[str, ...]) -> str | None:
    for attr in attrs:
        if not attr.startswith('xlabel="'):
            continue
        if not attr.endswith('"'):
            continue
        value = attr[len('xlabel="'):-1].strip()
        return value or None
    return None


def _looks_like_edge_numbering(value: str) -> bool:
    return bool(re.fullmatch(r"\d+\s*->\s*\d+", value))


def _append_route_rewrite_edges(
    *,
    source: str,
    target: str,
    route: Any,
    wrap_active: bool,
    wrapped_boundary: list[SppmSvgPostprocessEdge],
    rework_return: list[SppmSvgPostprocessEdge],
    rework_branch: list[SppmSvgPostprocessEdge],
) -> None:
    if route.is_boundary and not route.is_rework and wrap_active:
        edge_id = f"wrap_boundary:{source}:{target}"
        anchor_id: str | None = None
        if route.segments:
            first_leg_target = route.segments[0].target_id
            if first_leg_target.startswith("__wrap_exit_lr_"):
                anchor_id = first_leg_target
        wrapped_boundary.append(
            SppmSvgPostprocessEdge(
                edge_id=edge_id,
                source_id=source,
                target_id=target,
                anchor_id=anchor_id,
                edge_kind="wrap_boundary",
                expected_segment_count=len(route.segments),
            )
        )
        return

    if not route.is_rework or not route.anchors:
        return

    edge_id = f"rework:{_id_part(source)}:{_id_part(target)}"
    seg_count = len(route.segments)
    tail_side = _tailport_side(route.segments[0].attrs) if route.segments else None
    item = SppmSvgPostprocessEdge(
        edge_id=edge_id,
        source_id=source,
        target_id=target,
        anchor_id=route.anchors[0].anchor_id,
        edge_kind="rework_return" if tail_side in {"w", "n"} else "rework_branch",
        expected_segment_count=seg_count,
    )
    if item.edge_kind == "rework_return":
        rework_return.append(item)
    else:
        rework_branch.append(item)


def _append_decision_outcome_label_edge(
    *,
    source: str,
    target: str,
    route: Any,
    decision_outcome_labels: list[SppmSvgPostprocessEdge],
) -> None:
    for segment in getattr(route, "segments", ()):
        label_value = _xlabel_value(getattr(segment, "attrs", ()))
        if label_value is None or _looks_like_edge_numbering(label_value):
            continue
        decision_outcome_labels.append(
            SppmSvgPostprocessEdge(
                edge_id=f"decision_outcome:{_id_part(source)}:{_id_part(target)}",
                source_id=segment.source_id,
                target_id=segment.target_id,
                edge_kind="decision_outcome",
                expected_segment_count=1,
                anchor_id=source,
                label_text=label_value,
            )
        )
        return


def build_svg_postprocess_contract(
    *,
    routes: dict[tuple[str, str], Any],
    wrap_active: bool,
    node_kinds: dict[str, str] | None = None,
) -> SppmSvgPostprocessContract:
    """Build a postprocess contract from routing decisions.

    Accepts ``Any``-typed route values to avoid a circular import with the
    ``_sppm_routing`` module.  At runtime the values are ``SppmEdgeRoute``
    instances; their attributes are accessed via duck typing.
    """
    wrapped_boundary: list[SppmSvgPostprocessEdge] = []
    rework_return: list[SppmSvgPostprocessEdge] = []
    rework_branch: list[SppmSvgPostprocessEdge] = []
    decision_outcome_labels: list[SppmSvgPostprocessEdge] = []
    kinds = node_kinds or {}

    for (source, target), route in routes.items():
        _append_route_rewrite_edges(
            source=source,
            target=target,
            route=route,
            wrap_active=wrap_active,
            wrapped_boundary=wrapped_boundary,
            rework_return=rework_return,
            rework_branch=rework_branch,
        )
        if kinds.get(source) == "decision":
            _append_decision_outcome_label_edge(
                source=source,
                target=target,
                route=route,
                decision_outcome_labels=decision_outcome_labels,
            )
    return SppmSvgPostprocessContract(
        wrapped_boundary_edges=tuple(wrapped_boundary),
        rework_return_edges=tuple(rework_return),
        rework_branch_edges=tuple(rework_branch),
        decision_outcome_label_edges=tuple(decision_outcome_labels),
    )
