"""Edge rendering and rank-constraint helpers for the SPPM DOT renderer."""

from __future__ import annotations

from typing import Any

from ._graphviz_dot_common import _escape
from ._autoformat_wrap import WrapPlan
from ._sppm_secondary_line_constraints import (
    _collect_rework_pairs,
    _render_sppm_secondary_alignment_edges,
    _render_sppm_secondary_branch_track,
    _render_sppm_secondary_ordering_edges,
    _render_sppm_secondary_rank_subgraphs,
    _render_sppm_secondary_return_track,
)
from ._sppm_routing import SppmEdgeRoute, SppmRoutingPlan


def _render_sppm_edge(
    edge: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    options: Any,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    route: SppmEdgeRoute | None,
) -> list[str]:
    """Emit DOT lines for one SPPM edge (corridor nodes, anchors, segments)."""
    source = str(edge.get("source") or "")
    target = str(edge.get("target") or "")
    if not source or not target:
        return []
    if route is None:
        return []

    lines: list[str] = []
    for corridor_node in route.corridor_nodes:
        lines.append(f'  "{corridor_node.node_id}" [{", ".join(corridor_node.attrs)}];')
    for anchor in route.anchors:
        lines.append(f'  "{anchor.anchor_id}" [{", ".join(anchor.attrs)}];')
    for segment in route.segments:
        source_endpoint, target_endpoint, rendered_attrs = _materialize_sppm_segment(
            segment
        )
        lines.append(
            f"  {source_endpoint} -> {target_endpoint} "
            f"[{', '.join(_escape_sppm_route_attrs(rendered_attrs))}];"
        )
    return lines


def _materialize_sppm_segment(segment: Any) -> tuple[str, str, tuple[str, ...]]:
    """Resolve tail/head port attrs into DOT endpoint notation."""
    source_endpoint = f'"{_escape(segment.source_id)}"'
    target_endpoint = f'"{_escape(segment.target_id)}"'
    remaining_attrs: list[str] = []

    for attr in segment.attrs:
        if attr.startswith("tailport="):
            source_endpoint = _apply_port_attr_to_endpoint(source_endpoint, attr)
            continue
        if attr.startswith("headport="):
            target_endpoint = _apply_port_attr_to_endpoint(target_endpoint, attr)
            continue
        remaining_attrs.append(attr)

    return source_endpoint, target_endpoint, tuple(remaining_attrs)


def _apply_port_attr_to_endpoint(endpoint: str, attr: str) -> str:
    """Convert a ``tailport=`` or ``headport=`` attr into DOT colon notation."""
    _, raw_value = attr.split("=", 1)
    value = raw_value.strip().strip('"')
    if ":" not in value:
        return f"{endpoint}:{value}"

    port_name, compass = value.split(":", 1)
    return f'{endpoint}:"{_escape(port_name)}":{compass}'


def _render_sppm_spine_constraints(
    *,
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> list[str]:
    """Emit invisible high-weight constraints along the primary process spine."""
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if (source, target) in seen:
            continue
        route = routing_plan.route_for(source, target)
        if route is None or route.is_rework:
            continue
        seen.add((source, target))
        lines.append(
            f'  "{_escape(source)}" -> "{_escape(target)}" [style=invis, constraint=true, weight=80, minlen=1];'
        )
    return lines


def _render_sppm_secondary_line_constraints(
    *,
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> list[str]:
    """Emit invisible constraints for a stable secondary (rework) line.

    - Align each rework target with its local rework source column.
    - Chain rework targets left-to-right so they form a coherent lower lane.
    """
    rework_pairs, branch_anchor_pairs, return_anchor_pairs = _collect_rework_pairs(
        edges, routing_plan
    )

    if not rework_pairs:
        return []

    lines: list[str] = []

    lines.extend(_render_sppm_secondary_rank_subgraphs(rework_pairs))
    lines.extend(_render_sppm_secondary_alignment_edges(rework_pairs))
    lines.extend(_render_sppm_secondary_ordering_edges(rework_pairs))
    lines.extend(_render_sppm_secondary_branch_track(branch_anchor_pairs))
    lines.extend(_render_sppm_secondary_return_track(return_anchor_pairs))

    return lines


def _escape_sppm_route_attrs(attrs: tuple[str, ...]) -> list[str]:
    """Escape label values in route attrs while leaving other attrs unchanged."""
    escaped: list[str] = []
    for attr in attrs:
        if attr.startswith('label="') or attr.startswith('xlabel="'):
            prefix, value = attr.split('="', 1)
            escaped.append(f'{prefix}="{_escape(value[:-1])}"')
            continue
        escaped.append(attr)
    return escaped
