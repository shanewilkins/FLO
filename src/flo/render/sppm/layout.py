"""SPPM-owned ELK request construction and layout adapter."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from flo.render._diagnostics import log_render_diagnostics

from ..layout_core.elk import execute_elk_layout
from ..layout_core.elk_contracts import (
    ElkDirection,
    ElkLayoutEdge,
    ElkLayoutLane,
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
    sppm_nodes = ordered_nodes(
        nodes,
        options=render_options,
        size_resolver=_sppm_node_size,
    )
    wrap_plan = build_wrap_plan(nodes, render_options, planner="placement")
    if (
        direction == "RIGHT"
        and wrap_plan.chunks
        and _is_linear_sppm_sequence(nodes=nodes, edges=edge_specs)
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
        edge_specs = _apply_wrap_boundary_ports(
            edges=edge_specs,
            boundary_edges=wrap_plan.boundary_edges,
        )
    elif direction == "DOWN":
        lanes = lane_specs(
            process=process,
            nodes=nodes,
            separate_process_boundaries=False,
        )
        partition_overrides = {}
    else:
        synthetic_rows = _sppm_synthetic_row_lanes(nodes=nodes, edges=edge_specs)
        lanes = ()
        partition_overrides = _sppm_partition_indexes_for_synthetic_rows(
            node_ids=[node.id for node in sppm_nodes],
            lanes=synthetic_rows,
            edges=edge_specs,
        )
        edge_specs = _sppm_apply_secondary_row_edge_ports(
            edges=edge_specs,
            synthetic_rows=synthetic_rows,
            root_direction=direction,
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
    expected_edges = set(zip(node_ids, node_ids[1:]))
    actual_edges = {(edge.source_id, edge.target_id) for edge in edges}
    return (
        len(edges) == len(expected_edges)
        and actual_edges == expected_edges
        and not any(edge.is_rework for edge in edges)
    )


def _elk_direction(options: RenderOptions) -> ElkDirection:
    return "DOWN" if options.orientation == "tb" else "RIGHT"


__all__ = ["build_sppm_elk_layout_request", "layout_sppm_with_elk"]
