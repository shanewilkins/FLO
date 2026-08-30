"""Deterministic direct-SVG value-stream renderer."""

from __future__ import annotations

from html import escape
from typing import Any

from flo.process.analysis import ValueStreamFlow, project_value_stream
from flo.process.ir.models import IR

from ._artifact import RenderArtifact
from ._svg_shared_primitives import (
    SVG_ACCESSIBILITY_ATTRIBUTES,
    svg_accessibility_elements,
)
from .options import RenderOptions


_CARD_WIDTH = 170.0
_CARD_HEIGHT = 110.0
_CARD_GAP = 55.0
_CARD_TOP = 180.0


def render_value_stream_svg_artifact(
    process: Any, options: RenderOptions
) -> tuple[RenderArtifact, None]:
    """Render canonical item and timing facts as a value-stream SVG."""
    if not isinstance(process, IR):
        raise TypeError("value_stream rendering requires canonical IR")
    projection = project_value_stream(process)
    if not projection.nodes:
        raise ValueError(
            "value-stream-no-process-nodes: no task, queue, subprocess, system task, "
            "or decision nodes are available"
        )

    width = max(720.0, 90.0 + len(projection.nodes) * (_CARD_WIDTH + _CARD_GAP))
    height = 500.0
    positions = {
        node.node_id: 65.0 + index * (_CARD_WIDTH + _CARD_GAP)
        for index, node in enumerate(projection.nodes)
    }
    theme = options.resolved_theme
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" data-flo-artifact-kind="svg" data-flo-backend="svg" data-flo-diagram="value_stream" {SVG_ACCESSIBILITY_ATTRIBUTES}>',
        *svg_accessibility_elements(process, diagram_name="value stream map"),
        *_defs(options),
        f'<rect width="100%" height="100%" fill="{theme.canvas_background}" />',
        f'<text x="24" y="30" font-family="{theme.svg_font_family}" font-size="{theme.font_size(18)}" font-weight="700" fill="{theme.role("surface").title_text}">{escape(projection.process_name)}</text>',
        *_partial_notice(projection.diagnostics, options=options),
        *_surface_label("Information flow", y=92.0, options=options),
        *_surface_label("Material flow", y=348.0, options=options),
        *_render_flows(
            projection.information_flows,
            positions=positions,
            width=width,
            track_y=125.0,
            anchor_y=_CARD_TOP,
            marker="flo-vsm-information-arrow",
            role_name="information_route",
            dashed=True,
            options=options,
        ),
        *(
            part
            for node in projection.nodes
            for part in _node_card(node, x=positions[node.node_id], options=options)
        ),
        *_render_flows(
            projection.material_flows,
            positions=positions,
            width=width,
            track_y=370.0,
            anchor_y=_CARD_TOP + _CARD_HEIGHT,
            marker="flo-vsm-material-arrow",
            role_name="material_route",
            dashed=False,
            options=options,
        ),
        *_timeline(projection.modeled_lead_time_seconds, width=width, options=options),
        "</svg>",
    ]
    warning = _partial_warning(projection.diagnostics)
    return (
        RenderArtifact(
            kind="svg",
            content="\n".join(parts),
            backend="svg",
            metadata={
                "diagram": "value_stream",
                "partial": projection.partial,
                **({"warning": warning} if warning else {}),
            },
        ),
        None,
    )


def _defs(options: RenderOptions) -> list[str]:
    information = options.resolved_theme.role("information_route").border
    material = options.resolved_theme.role("material_route").border
    return [
        "<defs>",
        '<marker id="flo-vsm-information-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        f'<path d="M0,0 L8,3 L0,6 z" fill="{information}" />',
        "</marker>",
        '<marker id="flo-vsm-material-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto" markerUnits="strokeWidth">',
        f'<path d="M0,0 L8,3 L0,6 z" fill="{material}" />',
        "</marker>",
        "</defs>",
    ]


def _surface_label(label: str, *, y: float, options: RenderOptions) -> list[str]:
    role = options.resolved_theme.role("annotation")
    return [
        f'<text x="24" y="{y:.1f}" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(11)}" font-weight="700" fill="{role.detail_text}">{escape(label)}</text>'
    ]


def _partial_notice(
    diagnostics: tuple[Any, ...], *, options: RenderOptions
) -> list[str]:
    if not diagnostics:
        return []
    absent = ", ".join(
        diagnostic.code.removeprefix("value-stream-").removesuffix("-absent")
        for diagnostic in diagnostics
    )
    role = options.resolved_theme.role("callout")
    return [
        '<g data-flo-notice="partial-map">',
        f'<text x="24" y="55" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(11)}" font-weight="600" fill="{role.detail_text}">Partial map — no declared {escape(absent)} flow</text>',
        "</g>",
    ]


def _render_flows(
    flows: tuple[ValueStreamFlow, ...],
    *,
    positions: dict[str, float],
    width: float,
    track_y: float,
    anchor_y: float,
    marker: str,
    role_name: str,
    dashed: bool,
    options: RenderOptions,
) -> list[str]:
    role = options.resolved_theme.role(role_name)
    rendered: list[str] = []
    for index, flow in enumerate(flows):
        y = track_y + (index % 3) * (8.0 if anchor_y < track_y else -8.0)
        source_x = _flow_x(
            flow.source_node_id, positions=positions, width=width, source=True
        )
        target_x = _flow_x(
            flow.target_node_id, positions=positions, width=width, source=False
        )
        path = f"M {source_x:.1f},{anchor_y:.1f} V {y:.1f} H {target_x:.1f} V {anchor_y:.1f}"
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        rendered.extend(
            [
                f'<g data-flow-kind="{flow.kind}" data-item-id="{escape(flow.item_id, quote=True)}" data-source-node="{escape(flow.source_node_id or "external", quote=True)}" data-target-node="{escape(flow.target_node_id or "external", quote=True)}">',
                f'<path d="{path}" fill="none" stroke="{role.border}" stroke-width="2"{dash} marker-end="url(#{marker})" />',
                f'<text x="{(source_x + target_x) / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(10)}" fill="{role.detail_text}">{escape(flow.item_name)}</text>',
                "</g>",
            ]
        )
    return rendered


def _flow_x(
    node_id: str | None,
    *,
    positions: dict[str, float],
    width: float,
    source: bool,
) -> float:
    if node_id is None:
        return 36.0 if source else width - 36.0
    return positions[node_id] + _CARD_WIDTH / 2.0


def _node_card(node: Any, *, x: float, options: RenderOptions) -> list[str]:
    role_name = (
        "queue"
        if node.node_type == "queue"
        else "decision"
        if node.node_type == "decision"
        else "surface"
    )
    role = options.resolved_theme.role(role_name)
    metrics = _node_metrics(node)
    return [
        f'<g data-vsm-node-id="{escape(node.node_id, quote=True)}" data-node-type="{escape(node.node_type, quote=True)}">',
        f'<rect x="{x:.1f}" y="{_CARD_TOP:.1f}" width="{_CARD_WIDTH:.1f}" height="{_CARD_HEIGHT:.1f}" rx="5" fill="{role.fill}" stroke="{role.border}" stroke-width="1.5" />',
        f'<text x="{x + _CARD_WIDTH / 2:.1f}" y="{_CARD_TOP + 28:.1f}" text-anchor="middle" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(13)}" font-weight="700" fill="{role.title_text}">{escape(node.name)}</text>',
        f'<text x="{x + 12:.1f}" y="{_CARD_TOP + 57:.1f}" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(10)}" fill="{role.detail_text}">{escape(metrics[0])}</text>',
        f'<text x="{x + 12:.1f}" y="{_CARD_TOP + 76:.1f}" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(10)}" fill="{role.detail_text}">{escape(metrics[1])}</text>',
        f'<text x="{x + 12:.1f}" y="{_CARD_TOP + 95:.1f}" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(10)}" fill="{role.detail_text}">{escape(metrics[2])}</text>',
        "</g>",
    ]


def _node_metrics(node: Any) -> tuple[str, str, str]:
    return (
        _metric("CT", node.cycle_time_seconds),
        _metric("WT", node.wait_time_seconds),
        _metric("C/O", node.changeover_time_seconds),
    )


def _metric(label: str, seconds: float | None) -> str:
    if seconds is None:
        return f"{label} —"
    return f"{label} {_format_seconds(seconds)}"


def _format_seconds(seconds: float) -> str:
    if seconds and seconds % 3600 == 0:
        return f"{seconds / 3600:g} hr"
    if seconds and seconds % 60 == 0:
        return f"{seconds / 60:g} min"
    return f"{seconds:g} s"


def _timeline(
    lead_time: float | None, *, width: float, options: RenderOptions
) -> list[str]:
    role = options.resolved_theme.role("annotation")
    value = _format_seconds(lead_time) if lead_time is not None else "not derivable"
    return [
        f'<path d="M 65,430 H {width - 65:.1f}" stroke="{role.border}" stroke-width="1" />',
        f'<text x="65" y="453" font-family="{options.resolved_theme.svg_font_family}" font-size="{options.resolved_theme.font_size(11)}" font-weight="600" fill="{role.detail_text}">Modeled lead time: {escape(value)}</text>',
    ]


def _partial_warning(diagnostics: tuple[Any, ...]) -> str | None:
    if not diagnostics:
        return None
    codes = ", ".join(diagnostic.code for diagnostic in diagnostics)
    return f"value-stream-partial: {codes}"
