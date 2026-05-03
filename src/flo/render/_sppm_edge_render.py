"""Edge rendering and rank-constraint helpers for the SPPM DOT renderer."""

from __future__ import annotations

from typing import Any

from ._graphviz_dot_common import _escape
from ._autoformat_wrap import WrapPlan
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
        source_endpoint, target_endpoint, rendered_attrs = _materialize_sppm_segment(segment)
        lines.append(
            f'  {source_endpoint} -> {target_endpoint} '
            f'[{", ".join(_escape_sppm_route_attrs(rendered_attrs))}];'
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
            f'  "{_escape(source)}" -> "{_escape(target)}" [style=invis, constraint=true, weight=24];'
        )
    return lines


def _rework_target_ids(edges: list[dict[str, Any]], routing_plan: SppmRoutingPlan) -> set[str]:
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
            return_anchor_pairs.append((target, anchor_id))
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


def _render_sppm_secondary_line_constraints(
    *,
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> list[str]:
    """Emit invisible constraints for a stable secondary (rework) line.

    - Align each rework target with its local rework source column.
    - Chain rework targets left-to-right so they form a coherent lower lane.
    """
    rework_pairs, branch_anchor_pairs, return_anchor_pairs = _collect_rework_pairs(edges, routing_plan)

    if not rework_pairs:
        return []

    lines: list[str] = []

    # Column-align each rework task with its branch source in LR layout.
    for idx, (source, target) in enumerate(rework_pairs):
        lines.append(f"  subgraph sppm_secondary_rank_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(source)}";')
        lines.append(f'    "{_escape(target)}";')
        lines.append("  }")

    # High-weight invis edges attract rework nodes toward their branch sources in Y.
    for source, target in rework_pairs:
        lines.append(
            f'  "{_escape(source)}" -> "{_escape(target)}" [style=invis, constraint=false, weight=50, minlen=0];'
        )

    # Keep the secondary line ordered and compact.
    ordered_targets = [target for _, target in rework_pairs]
    for left, right in zip(ordered_targets, ordered_targets[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=true, weight=16, minlen=1];'
        )

    # Shared branch-out track: align and chain branch anchors.
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

    # Return anchors: chain only (no rank=same); SVG postprocessor pins paths.
    ordered_return_anchors = [anchor_id for _, anchor_id in return_anchor_pairs]
    for left, right in zip(ordered_return_anchors, ordered_return_anchors[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=false, weight=0, minlen=1];'
        )

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
