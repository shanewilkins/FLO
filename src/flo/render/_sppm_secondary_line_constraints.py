"""Support helpers for SPPM secondary line constraints."""

from __future__ import annotations

from typing import Any

from ._graphviz_dot_common import _escape
from ._sppm_routing import SppmRoutingPlan


def _rework_target_ids(
    edges: list[dict[str, Any]], routing_plan: SppmRoutingPlan
) -> set[str]:
    """Return the set of node IDs that are targets of any rework edge."""
    result: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        route = routing_plan.route_for(source, target)
        if route is not None and route.is_rework:
            result.add(target)
    return result


def _accumulate_rework_edge(
    *,
    edge: dict[str, Any],
    routing_plan: SppmRoutingPlan,
    all_rework_targets: set[str],
    seen_targets: set[str],
    rework_pairs: list[tuple[str, str]],
    branch_anchor_pairs: list[tuple[str, str]],
    return_anchor_pairs: list[tuple[str, str]],
) -> None:
    """Classify and accumulate one edge into the appropriate rework pair lists."""
    source = str(edge.get("source") or "")
    target = str(edge.get("target") or "")
    if not source or not target:
        return
    route = routing_plan.route_for(source, target)
    if route is None or not route.is_rework:
        return
    anchor_id = route.anchors[0].anchor_id if route.anchors else ""
    if source in all_rework_targets:
        if anchor_id:
            return_anchor_pairs.append((source, anchor_id))
        return
    if target in seen_targets:
        return
    seen_targets.add(target)
    rework_pairs.append((source, target))
    if anchor_id:
        branch_anchor_pairs.append((target, anchor_id))


def _collect_rework_pairs(
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """Classify rework edges into branch, return, and alignment pairs.

    Returns ``(rework_pairs, branch_anchor_pairs, return_anchor_pairs)`` where
    each element is a list of ``(node_id, anchor_id)`` or ``(source, target)``
    tuples used to emit rank/chain constraints.
    """
    all_rework_targets = _rework_target_ids(edges, routing_plan)
    rework_pairs: list[tuple[str, str]] = []
    branch_anchor_pairs: list[tuple[str, str]] = []
    return_anchor_pairs: list[tuple[str, str]] = []
    seen_targets: set[str] = set()

    for edge in edges:
        _accumulate_rework_edge(
            edge=edge,
            routing_plan=routing_plan,
            all_rework_targets=all_rework_targets,
            seen_targets=seen_targets,
            rework_pairs=rework_pairs,
            branch_anchor_pairs=branch_anchor_pairs,
            return_anchor_pairs=return_anchor_pairs,
        )

    return rework_pairs, branch_anchor_pairs, return_anchor_pairs


def _render_sppm_secondary_rank_subgraphs(
    rework_pairs: list[tuple[str, str]],
) -> list[str]:
    """Render the rank-same subgraphs that align rework branches."""
    lines: list[str] = []
    for idx, (source, target) in enumerate(rework_pairs):
        lines.append(f"  subgraph sppm_secondary_rank_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(source)}";')
        lines.append(f'    "{_escape(target)}";')
        lines.append("  }")
    return lines


def _render_sppm_secondary_alignment_edges(
    rework_pairs: list[tuple[str, str]],
) -> list[str]:
    """Render the invisible edges that attract rework nodes toward their branches."""
    lines: list[str] = []
    for source, target in rework_pairs:
        lines.append(
            f'  "{_escape(source)}" -> "{_escape(target)}" [style=invis, constraint=false, weight=50, minlen=0];'
        )
    return lines


def _render_sppm_secondary_ordering_edges(
    rework_pairs: list[tuple[str, str]],
) -> list[str]:
    """Render the invisible edges that keep rework nodes ordered."""
    lines: list[str] = []
    ordered_targets = [target for _, target in rework_pairs]
    for left, right in zip(ordered_targets, ordered_targets[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=true, weight=16, minlen=1];'
        )
    return lines


def _render_sppm_secondary_branch_track(
    branch_anchor_pairs: list[tuple[str, str]],
) -> list[str]:
    """Render the branch-out track that keeps branch anchors aligned."""
    lines: list[str] = []
    for idx, (target, anchor_id) in enumerate(branch_anchor_pairs):
        lines.append(f"  subgraph sppm_secondary_branch_track_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(target)}";')
        lines.append(f'    "{_escape(anchor_id)}";')
        lines.append("  }")
        lines.append(
            f'  "{_escape(anchor_id)}" -> "{_escape(target)}" [style=invis, constraint=false, weight=50, minlen=0];'
        )
    ordered_branch_anchors = [anchor_id for _, anchor_id in branch_anchor_pairs]
    for left, right in zip(ordered_branch_anchors, ordered_branch_anchors[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=false, weight=0, minlen=1];'
        )
    return lines


def _render_sppm_secondary_return_track(
    return_anchor_pairs: list[tuple[str, str]],
) -> list[str]:
    """Render the return-loop track that keeps anchors beside return sources."""
    lines: list[str] = []
    for idx, (source, anchor_id) in enumerate(return_anchor_pairs):
        lines.append(f"  subgraph sppm_secondary_return_track_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(source)}";')
        lines.append(f'    "{_escape(anchor_id)}";')
        lines.append("  }")
        lines.append(
            f'  "{_escape(source)}" -> "{_escape(anchor_id)}" [style=invis, constraint=false, weight=50, minlen=0];'
        )
    return lines
