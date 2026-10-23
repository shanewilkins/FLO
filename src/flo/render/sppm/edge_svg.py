"""Serialize attached connectors and positioned annotations without layout policy."""

from __future__ import annotations

from html import escape
from typing import Any

from .._execution import AttachedEdge, EdgeAnnotation
from ..options import RenderOptions


def _edge_stroke(
    edge_path: Any,
    *,
    render_as_rework_style: bool = False,
) -> tuple[str, str | None, float]:
    if not bool(edge_path.is_rework or render_as_rework_style):
        return "#475569", None, 2.5
    variant = str(edge_path.rework_variant or "")
    if variant == "branch":
        return "#b91c1c", "2 6", 2.6
    if variant == "return":
        return "#c2410c", "2 6", 2.4
    return "#b91c1c", "2 6", 2.5


def _edge_variant_attr(rework_variant: str) -> str:
    if not rework_variant:
        return ""
    return f' data-edge-rework-variant="{escape(rework_variant)}"'


def emit_edge(edge: AttachedEdge, options: RenderOptions) -> list[str]:
    """Paint supplied points and annotation bounds without choosing positions."""
    if len(edge.points) < 2:
        return []
    polyline = " ".join(f"{p.x_px:.1f},{p.y_px:.1f}" for p in edge.points)
    edge_kind = "rework" if edge.rework else "direct"
    width = (
        2.6
        if edge.variant == "branch" and edge.rework
        else 2.4
        if edge.variant == "return" and edge.rework
        else 2.5
    )
    stroke = options.resolved_theme.role(
        "rework" if edge.rework else "connector"
    ).border
    dash = ' stroke-dasharray="2 6"' if edge.rework else ""
    marker = "flo-sppm-rework-arrow" if edge.rework else "flo-sppm-arrow"
    parts = [
        f'<g data-edge-source="{escape(edge.edge[0])}" data-edge-target="{escape(edge.edge[1])}" data-edge-kind="{edge_kind}"{_edge_variant_attr(edge.variant)}>',
        f'<polyline points="{polyline}" fill="none" stroke="{stroke}" stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"{dash} />',
    ]
    for annotation in edge.annotations:
        parts.extend(emit_annotation(annotation, options))
    parts.append("</g>")
    return parts


def emit_annotation(annotation: EdgeAnnotation, options: RenderOptions) -> list[str]:
    """Serialize already placed annotation rectangles and text runs."""
    box = annotation.bounds
    if annotation.kind == "label":
        role = options.resolved_theme.role("annotation")
        text = annotation.texts[0]
        return [
            f'<rect x="{box.x_px:.1f}" y="{box.y_px:.1f}" width="{box.width_px:.1f}" height="{box.height_px:.1f}" rx="7" fill="{role.fill}" fill-opacity="0.95" />',
            f'<text x="{text.x:.1f}" y="{text.y:.1f}" text-anchor="{text.anchor}" font-family="Helvetica" font-size="{text.size_px}" fill="{role.title_text}">{escape(text.text)}</text>',
        ]
    if annotation.kind == "callout":
        role = options.resolved_theme.role("callout")
        return [
            f'<rect x="{box.x_px:.1f}" y="{box.y_px:.1f}" width="{box.width_px:.1f}" height="{box.height_px:.1f}" rx="7" fill="{role.fill}" stroke="{role.border}" stroke-width="1" fill-opacity="0.96" />',
            *(
                f'<text x="{text.x:.1f}" y="{text.y:.1f}" text-anchor="{text.anchor}" font-family="Helvetica" font-size="{text.size_px}" font-weight="{text.weight}" fill="{role.title_text}">{escape(text.text)}</text>'
                for text in annotation.texts
            ),
        ]
    role = options.resolved_theme.role("token")
    text = annotation.texts[0]
    return [
        f'<g data-edge-token="{escape(annotation.token or "")}" data-edge-token-position="{annotation.token_position}">',
        f'<rect x="{box.x_px:.1f}" y="{box.y_px:.1f}" width="{box.width_px:.1f}" height="{box.height_px:.1f}" rx="11" fill="{role.fill}" stroke="{role.border}" stroke-width="1.2" />',
        f'<text x="{text.x:.1f}" y="{text.y:.1f}" text-anchor="{text.anchor}" font-family="Helvetica" font-size="{text.size_px}" font-weight="{text.weight}" fill="{role.detail_text}">{escape(text.text)}</text>',
        "</g>",
    ]
