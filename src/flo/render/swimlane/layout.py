"""Swimlane-owned ELK request construction and layout adapter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flo.render._diagnostics import log_render_diagnostics

from ..layout_core.elk import execute_elk_layout
from ..layout_core.elk_contracts import ElkDirection, ElkLayoutRequest
from ..layout_core.elk_runtime import run_elkjs_layout
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


def build_swimlane_elk_layout_request(
    process: dict[str, Any] | Any, options: RenderOptions | None = None
) -> ElkLayoutRequest:
    """Build an ELK request for the swimlane renderer."""
    render_options = options or RenderOptions(diagram="swimlane")
    if render_options.diagram != "swimlane":
        raise ValueError("Swimlane ELK request builder requires diagram='swimlane'.")

    nodes, edges = extract_nodes_and_edges(process)
    if render_options.subprocess_view == "parent_only":
        nodes, edges = project_parent_only_subprocess_view(nodes, edges)

    direction = _elk_direction(render_options)
    request = ElkLayoutRequest(
        diagram="swimlane",
        direction=direction,
        lanes=lane_specs(process=process, nodes=nodes),
        nodes=ordered_nodes(nodes, options=render_options),
        edges=ordered_edges(
            edges,
            node_kinds=_node_kind_map(nodes),
            diagram="swimlane",
            direction=direction,
        ),
        strict_diagnostics=render_options.layout_fit == "fit-strict",
    )
    validate_elk_request_namespaces(request)
    return request


def layout_swimlane_with_elk(
    process: dict[str, Any] | Any,
    *,
    engine: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    options: RenderOptions | None = None,
) -> LayoutResult:
    """Build, execute, and normalize a swimlane ELK layout pass."""
    render_options = options or RenderOptions(diagram="swimlane")
    if render_options.diagram != "swimlane":
        raise ValueError("Swimlane ELK adapter requires diagram='swimlane'.")

    request = build_swimlane_elk_layout_request(process, options=render_options)
    result = execute_elk_layout(request, engine=engine or run_elkjs_layout)
    diagnostics_report = result.diagnostics_report(
        diagram="swimlane",
        backend="elk",
        artifact_kind="layout_result",
        strict=render_options.layout_fit == "fit-strict",
    )
    log_render_diagnostics(diagnostics_report)
    return result


def _node_kind_map(nodes: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(node.get("id") or ""): str(node.get("kind") or "task")
        for node in nodes
        if str(node.get("id") or "")
    }


def _elk_direction(options: RenderOptions) -> ElkDirection:
    return "DOWN" if options.orientation == "tb" else "RIGHT"


__all__ = ["build_swimlane_elk_layout_request", "layout_swimlane_with_elk"]
