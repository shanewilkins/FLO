"""SPPM SVG postprocess contract types.

Stable, renderer-owned data that tells the SVG postprocessor exactly which
edges to rewrite without relying on fragile DOT text or SVG title matching.
"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SppmSvgPostprocessContract:
    """Manifest of expected SVG edge rewrites for one SPPM diagram.

    Built by the routing layer and passed through to the SVG postprocessor,
    replacing regex-based DOT/SVG scanning with an explicit edge registry.
    """

    wrapped_boundary_edges: tuple[SppmSvgPostprocessEdge, ...] = ()
    rework_return_edges: tuple[SppmSvgPostprocessEdge, ...] = ()
    rework_branch_edges: tuple[SppmSvgPostprocessEdge, ...] = ()


def build_svg_postprocess_contract(
    *,
    routes: dict[tuple[str, str], Any],
    wrap_active: bool,
) -> SppmSvgPostprocessContract:
    """Build a postprocess contract from routing decisions.

    Accepts ``Any``-typed route values to avoid a circular import with the
    ``_sppm_routing`` module.  At runtime the values are ``SppmEdgeRoute``
    instances; their attributes are accessed via duck typing.
    """
    def _id_part(s: str) -> str:
        return "".join(c if c.isalnum() or c == "_" else "_" for c in s) or "edge"

    wrapped_boundary: list[SppmSvgPostprocessEdge] = []
    rework_return: list[SppmSvgPostprocessEdge] = []
    rework_branch: list[SppmSvgPostprocessEdge] = []
    for (source, target), route in routes.items():
        if route.is_boundary and not route.is_rework and wrap_active:
            edge_id = f"wrap_boundary:{source}:{target}"
            wrapped_boundary.append(SppmSvgPostprocessEdge(
                edge_id=edge_id, source_id=source, target_id=target,
                edge_kind="wrap_boundary", expected_segment_count=len(route.segments),
            ))
        elif route.is_rework and route.anchors:
            edge_id = f"rework:{_id_part(source)}:{_id_part(target)}"
            seg_count = len(route.segments)
            rework_branch.append(SppmSvgPostprocessEdge(
                edge_id=edge_id, source_id=source, target_id=target,
                edge_kind="rework_branch", expected_segment_count=seg_count,
            ))
            rework_return.append(SppmSvgPostprocessEdge(
                edge_id=edge_id, source_id=source, target_id=target,
                edge_kind="rework_return", expected_segment_count=seg_count,
            ))
    return SppmSvgPostprocessContract(
        wrapped_boundary_edges=tuple(wrapped_boundary),
        rework_return_edges=tuple(rework_return),
        rework_branch_edges=tuple(rework_branch),
    )
