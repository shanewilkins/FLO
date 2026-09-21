"""SPPM-owned ELK request construction and layout adapter."""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from flo.render._diagnostics import log_render_diagnostics

from ..layout_core.elk import execute_elk_layout
from ..layout_core.elk_contracts import (
    ElkDirection,
    ElkLayoutEdge,
    ElkLayoutLane,
    ElkLayoutNode,
    ElkLayoutRequest,
)
from ..layout_core.elk_runtime import run_elkjs_layout
from ..layout_core.elk_sppm_helpers import (
    _node_kind_map,
    _sppm_apply_secondary_row_edge_ports,
    _sppm_partition_indexes_for_synthetic_rows,
    _sppm_synthetic_row_lanes,
)
from ..layout_core.elk_support import (
    extract_nodes_and_edges,
    ordered_edges,
    ordered_nodes,
    project_parent_only_subprocess_view,
)
from ..layout_core.elk_validation import validate_elk_request_namespaces
from ..layout_core.lane_support import lane_specs
from ..layout_core.models import LayoutResult
from ..options import RenderOptions
from .content import measure_sppm_node
from .continuation_tokens import resolve_explicit_sppm_continuation_tokens
from .rework_content import build_sppm_rework_metadata_lines
from .wrap import build_wrap_plan


def build_sppm_elk_layout_request(
    process: dict[str, Any] | Any, options: RenderOptions | None = None
) -> ElkLayoutRequest:
    """Build an ELK layout request containing SPPM-owned presentation data."""
    render_options = options or RenderOptions(diagram="sppm")
    if render_options.diagram != "sppm":
        raise ValueError("SPPM ELK request builder requires diagram='sppm'.")

    nodes, edges = extract_nodes_and_edges(process)
    if render_options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)

    direction = _elk_direction(render_options)
    edge_specs = ordered_edges(
        edges,
        node_kinds=_node_kind_map(nodes),
        diagram="sppm",
        direction=direction,
        decorator=_decorate_sppm_edge,
    )
    edge_specs = _derive_rework_branch_routes(
        edges=edge_specs,
        node_kinds=_node_kind_map(nodes),
    )
    sppm_nodes = ordered_nodes(
        nodes,
        options=render_options,
        size_resolver=_sppm_node_size,
    )
    lanes, partition_overrides, edge_specs = _resolve_sppm_lanes(
        process=process,
        nodes=nodes,
        sppm_nodes=sppm_nodes,
        edges=edge_specs,
        direction=direction,
        options=render_options,
    )

    request = ElkLayoutRequest(
        diagram="sppm",
        direction=direction,
        lanes=lanes,
        nodes=tuple(
            replace(
                node,
                partition_index=partition_overrides.get(node.id, node.partition_index),
            )
            for node in sppm_nodes
        ),
        edges=edge_specs,
        strict_diagnostics=render_options.layout_fit == "fit-strict",
    )
    validate_elk_request_namespaces(request)
    return request


def _resolve_sppm_lanes(
    *,
    process: dict[str, Any] | Any,
    nodes: list[dict[str, Any]],
    sppm_nodes: tuple[ElkLayoutNode, ...],
    edges: tuple[ElkLayoutEdge, ...],
    direction: ElkDirection,
    options: RenderOptions,
) -> tuple[tuple[ElkLayoutLane, ...], dict[str, int], tuple[ElkLayoutEdge, ...]]:
    """Resolve SPPM rows, partitions, and any wrap-boundary edge ports."""
    synthetic_rows = (
        _sppm_synthetic_row_lanes(nodes=nodes, edges=edges)
        if direction == "RIGHT"
        else ()
    )
    branched_wrap = _explicit_branched_wrap_lanes(
        nodes=nodes,
        options=options,
        synthetic_rows=synthetic_rows,
    )
    if branched_wrap is not None:
        lanes, boundary_edges = branched_wrap
        partition_overrides = {
            node_id: display_index
            for lane in lanes
            for display_index, node_id in enumerate(lane.node_ids)
        }
        return (
            lanes,
            partition_overrides,
            _apply_wrap_boundary_ports(edges=edges, boundary_edges=boundary_edges),
        )

    wrap_plan = build_wrap_plan(nodes, options, planner="placement")
    if (
        direction == "RIGHT"
        and wrap_plan.chunks
        and _is_linear_sppm_sequence(nodes=nodes, edges=edges)
    ):
        lanes = tuple(
            ElkLayoutLane(
                id=f"__sppm_row_wrap_{row_index}",
                label="",
                node_ids=tuple(chunk),
            )
            for row_index, chunk in enumerate(wrap_plan.chunks)
        )
        partition_overrides = {
            node_id: display_index
            for chunk in wrap_plan.chunks
            for display_index, node_id in enumerate(chunk)
        }
        return (
            lanes,
            partition_overrides,
            _apply_wrap_boundary_ports(
                edges=edges,
                boundary_edges=wrap_plan.boundary_edges,
            ),
        )

    if direction == "DOWN":
        return (
            lane_specs(
                process=process,
                nodes=nodes,
                separate_process_boundaries=False,
            ),
            {},
            edges,
        )

    partition_overrides = _sppm_partition_indexes_for_synthetic_rows(
        node_ids=[node.id for node in sppm_nodes],
        lanes=synthetic_rows,
        edges=edges,
    )
    return (
        (),
        partition_overrides,
        _sppm_apply_secondary_row_edge_ports(
            edges=edges,
            synthetic_rows=synthetic_rows,
            root_direction=direction,
            partition_indexes=partition_overrides,
        ),
    )


def _explicit_branched_wrap_lanes(
    *,
    nodes: list[dict[str, Any]],
    options: RenderOptions,
    synthetic_rows: tuple[ElkLayoutLane, ...],
) -> tuple[tuple[ElkLayoutLane, ...], set[tuple[str, str]]] | None:
    """Wrap a rework graph only when the caller requested an exact width."""
    if options.layout_width_px is None or len(synthetic_rows) < 2:
        return None
    mainline_lane = next(
        (lane for lane in synthetic_rows if lane.id == "__sppm_row_mainline"),
        None,
    )
    rework_lane = next(
        (lane for lane in synthetic_rows if lane.id == "__sppm_row_rework"),
        None,
    )
    if mainline_lane is None or rework_lane is None:
        return None

    mainline_ids = set(mainline_lane.node_ids)
    mainline_nodes = [
        node for node in nodes if str(node.get("id") or "") in mainline_ids
    ]
    plan = build_wrap_plan(mainline_nodes, options, planner="placement")
    if not plan.chunks:
        return None

    # Keep the secondary rework path below every wrapped mainline row so
    # ordinary continuation edges never have to pass through rework nodes.
    rework_after_row = len(plan.chunks) - 1

    lanes: list[ElkLayoutLane] = []
    for row_index, chunk in enumerate(plan.chunks):
        lanes.append(
            ElkLayoutLane(
                id=f"__sppm_row_wrap_{len(lanes)}",
                label="",
                node_ids=tuple(chunk),
            )
        )
        if row_index == rework_after_row:
            lanes.append(
                ElkLayoutLane(
                    id=f"__sppm_row_wrap_rework_{len(lanes)}",
                    label="",
                    node_ids=rework_lane.node_ids,
                )
            )

    return tuple(lanes), plan.boundary_edges


def layout_sppm_with_elk(
    process: dict[str, Any] | Any,
    *,
    engine: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    options: RenderOptions | None = None,
) -> LayoutResult:
    """Build, execute, and normalize an SPPM ELK layout pass."""
    render_options = options or RenderOptions(diagram="sppm")
    if render_options.diagram != "sppm":
        raise ValueError("SPPM ELK adapter requires diagram='sppm'.")

    request = build_sppm_elk_layout_request(process, options=render_options)
    result = execute_elk_layout(request, engine=engine or run_elkjs_layout)
    diagnostics_report = result.diagnostics_report(
        diagram="sppm",
        backend="elk",
        artifact_kind="layout_result",
        strict=render_options.layout_fit == "fit-strict",
    )
    log_render_diagnostics(diagnostics_report)
    return result


def _sppm_node_size(node: dict[str, Any], options: RenderOptions) -> tuple[int, int]:
    node_id = str(node.get("id") or "")
    measure = measure_sppm_node(
        node_id=node_id,
        kind=str(node.get("kind") or ""),
        name=str(node.get("name") or node_id),
        metadata=node.get("metadata") or {},
        workers=node.get("workers") or [],
        note=str(node.get("note") or ""),
        options=options,
    )
    return measure.width_px, measure.height_px


def _decorate_sppm_edge(edge: ElkLayoutEdge, raw_edge: dict[str, Any]) -> ElkLayoutEdge:
    outgoing_token, incoming_token = resolve_explicit_sppm_continuation_tokens(raw_edge)
    callout_lines = (
        build_sppm_rework_metadata_lines(raw_edge.get("metadata"))
        if edge.is_rework
        else ()
    )
    return replace(
        edge,
        callout_lines=callout_lines,
        callout_near_source=bool(callout_lines and edge.label),
        outgoing_token=outgoing_token,
        incoming_token=incoming_token,
    )


def _derive_rework_branch_routes(
    *,
    edges: tuple[ElkLayoutEdge, ...],
    node_kinds: dict[str, str],
) -> tuple[ElkLayoutEdge, ...]:
    """Mark ordinary decision paths that lead to an explicit rework return."""
    return_sources = {
        edge.source_id
        for edge in edges
        if edge.is_rework and edge.rework_variant == "return"
    }
    if not return_sources:
        return edges

    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        if edge.is_rework:
            continue
        adjacency.setdefault(edge.source_id, set()).add(edge.target_id)

    def reaches_return_source(start_id: str) -> bool:
        visited: set[str] = set()
        frontier = [start_id]
        while frontier:
            node_id = frontier.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            if node_id in return_sources:
                return True
            if node_id != start_id and node_kinds.get(node_id) == "decision":
                continue
            frontier.extend(sorted(adjacency.get(node_id, ()), reverse=True))
        return False

    derived: list[ElkLayoutEdge] = []
    for edge in edges:
        if (
            not edge.is_rework
            and node_kinds.get(edge.source_id) == "decision"
            and reaches_return_source(edge.target_id)
        ):
            derived.append(
                replace(
                    edge,
                    rework_variant="branch",
                    source_port_side="SOUTH",
                    target_port_side="NORTH",
                )
            )
            continue
        derived.append(edge)
    return tuple(derived)


def _apply_wrap_boundary_ports(
    *,
    edges: tuple[ElkLayoutEdge, ...],
    boundary_edges: set[tuple[str, str]],
) -> tuple[ElkLayoutEdge, ...]:
    return tuple(
        replace(edge, source_port_side="SOUTH", target_port_side="NORTH")
        if (edge.source_id, edge.target_id) in boundary_edges and not edge.is_rework
        else edge
        for edge in edges
    )


def _is_linear_sppm_sequence(
    *, nodes: list[dict[str, Any]], edges: tuple[ElkLayoutEdge, ...]
) -> bool:
    node_ids = [str(node.get("id") or "") for node in nodes]
    if not node_ids or any(not node_id for node_id in node_ids):
        return False
    expected_edges = set(itertools.pairwise(node_ids))
    actual_edges = {(edge.source_id, edge.target_id) for edge in edges}
    return (
        len(edges) == len(expected_edges)
        and actual_edges == expected_edges
        and not any(edge.is_rework for edge in edges)
    )


def _elk_direction(options: RenderOptions) -> ElkDirection:
    return "DOWN" if options.orientation == "tb" else "RIGHT"


__all__ = ["build_sppm_elk_layout_request", "layout_sppm_with_elk"]
