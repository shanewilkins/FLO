"""Node SVG generation helpers for direct SPPM rendering."""

from __future__ import annotations

from html import escape
from typing import Any

from ._sppm_node_appearance import resolve_sppm_node_appearance
from ._sppm_node_content import build_sppm_node_content
from ._sppm_task_card import build_sppm_task_card_layout
from .options import RenderOptions


def _node_svg(
    *,
    node: Any,
    raw_node: dict[str, Any],
    options: RenderOptions,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    kind = str(node.kind or "task").lower()
    content = build_sppm_node_content(
        node_id=str(node.id),
        kind=kind,
        name=str(node.label or node.id),
        metadata=raw_node.get("metadata") or {},
        workers=raw_node.get("workers") or [],
        note=str(raw_node.get("note") or ""),
        options=options,
    )
    appearance = resolve_sppm_node_appearance(
        kind=kind,
        metadata=raw_node.get("metadata") or {},
        options=options,
    )
    parts = [f'<g data-node-id="{escape(node.id)}" data-node-kind="{escape(kind)}">']
    title_lines = tuple(line for line in str(content.title).split("\n") if line)
    info_lines = content.info_lines
    task_card = (
        build_sppm_task_card_layout(content)
        if kind not in {"decision", "queue", "subprocess", "start", "end"}
        else None
    )

    label_start_y, header_height = _append_node_shape_svg(
        parts=parts,
        kind=kind,
        title_lines=title_lines,
        info_lines=info_lines,
        appearance=appearance,
        task_card=task_card,
        x=x,
        y=y,
        width=width,
        height=height,
    )

    parts.extend(
        _text_lines_svg(
            x=x + (width / 2.0),
            y=label_start_y,
            lines=title_lines,
            size_px=14,
            weight="600",
            fill="#0f172a" if kind == "queue" else appearance.title_fill,
            line_gap_px=16.0,
            anchor="middle",
        )
    )
    parts.extend(
        _node_info_lines_svg(
            kind=kind,
            info_lines=info_lines,
            title_lines=title_lines,
            label_start_y=label_start_y,
            header_height=header_height,
            appearance=appearance,
            task_card=task_card,
            x=x,
            y=y,
            width=width,
            height=height,
        )
    )
    parts.append("</g>")
    return parts


def _append_node_shape_svg(
    *,
    parts: list[str],
    kind: str,
    title_lines: tuple[str, ...],
    info_lines: tuple[str, ...],
    appearance: Any,
    task_card: Any,
    x: float,
    y: float,
    width: float,
    height: float,
) -> tuple[float, float | None]:
    if kind == "decision":
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)
        parts.append(
            f'<polygon points="{cx:.1f},{y:.1f} {x + width:.1f},{cy:.1f} {cx:.1f},{y + height:.1f} {x:.1f},{cy:.1f}" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2" />'
        )
        return cy - ((_line_count(title_lines) - 1) * 8.0) + 5.0, None
    if kind == "queue":
        cx = x + (width / 2.0)
        label_band_height = min(32.0, height * 0.24)
        label_band_top = y + height - label_band_height
        inset = (label_band_height / height) * (width / 2.0)
        parts.append(
            f'<polygon data-node-queue-body="true" points="{x:.1f},{y + height:.1f} {x + width:.1f},{y + height:.1f} {cx:.1f},{y:.1f}" fill="#ffffff" stroke="{appearance.border}" stroke-width="2" />'
        )
        parts.append(
            f'<polygon data-node-queue-label-band="true" points="{x:.1f},{y + height:.1f} {x + width:.1f},{y + height:.1f} {x + width - inset:.1f},{label_band_top:.1f} {x + inset:.1f},{label_band_top:.1f}" fill="{appearance.fill}" stroke="none" />'
        )
        return (
            label_band_top
            + (label_band_height / 2.0)
            + 5.0
            - ((_line_count(title_lines) - 1) * 8.0),
            None,
        )
    if kind == "subprocess":
        cx = x + (width / 2.0)
        cy = y + (height / 2.0)
        rx = width / 2.0
        ry = height / 2.0
        dash_attr = (
            f' stroke-dasharray="{appearance.stroke_dasharray}"'
            if appearance.stroke_dasharray
            else ""
        )
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2"{dash_attr} />'
        )
        return y + 24.0, None
    if kind in {"start", "end"}:
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="18" fill="{appearance.fill}" stroke="{appearance.border}" stroke-width="2" />'
        )
        return y + (height / 2.0) - ((_line_count(title_lines) - 1) * 8.0) + 5.0, None

    parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="12" fill="white" stroke="{appearance.border}" stroke-width="2" />'
    )
    header_height = max(28.0, 18.0 + (_line_count(title_lines) * 16.0))
    header_radius = min(12.0, width / 2.0, header_height)
    parts.append(
        f'<path data-node-header="top-rounded" d="{_top_rounded_header_path(x=x, y=y, width=width, height=header_height, radius=header_radius)}" fill="{appearance.fill}" stroke="none" />'
    )
    if info_lines:
        parts.append(
            f'<line x1="{x:.1f}" y1="{y + header_height:.1f}" x2="{x + width:.1f}" y2="{y + header_height:.1f}" stroke="{appearance.border}" stroke-width="1" opacity="0.35" />'
        )
    return y + 18.0, header_height


def _node_info_lines_svg(
    *,
    kind: str,
    info_lines: tuple[str, ...],
    title_lines: tuple[str, ...],
    label_start_y: float,
    header_height: float | None,
    appearance: Any,
    task_card: Any,
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[str]:
    if not info_lines:
        return []
    if kind == "queue":
        info_line_count = _line_count(info_lines)
        info_start_y = max(
            y + 26.0,
            (y + (height * 0.34)) - ((info_line_count - 1) * 6.5),
        )
        return _text_lines_svg(
            x=x + (width / 2.0),
            y=info_start_y,
            lines=info_lines,
            size_px=11,
            weight="400",
            fill="#0f172a",
            line_gap_px=13.0,
            anchor="middle",
        )
    if kind == "subprocess":
        return _text_lines_svg(
            x=x + (width / 2.0),
            y=label_start_y + (_line_count(title_lines) * 15.0) + 6.0,
            lines=info_lines,
            size_px=11,
            weight="400",
            fill=appearance.info_fill,
            line_gap_px=13.0,
            anchor="middle",
        )
    if kind in {"decision", "start", "end"}:
        return []

    body_text_x = x + 12.0
    if task_card is not None:
        body_text_x = (
            x
            + task_card.gutter_width_px
            + task_card.body_padding_px
            + task_card.body_text_offset_px
        )
    effective_header_height = header_height or max(
        28.0, 18.0 + (_line_count(title_lines) * 16.0)
    )
    return _text_lines_svg(
        x=body_text_x,
        y=y + effective_header_height + 18.0,
        lines=info_lines,
        size_px=11,
        weight="400",
        fill=appearance.info_fill,
        line_gap_px=13.0,
        anchor="start",
    )


def _text_lines_svg(
    *,
    x: float,
    y: float,
    lines: tuple[str, ...],
    size_px: int,
    weight: str,
    fill: str,
    line_gap_px: float,
    anchor: str,
) -> list[str]:
    if not lines:
        return []
    parts: list[str] = []
    current_y = y
    for line in lines:
        for subline in [segment for segment in line.split("\n") if segment]:
            parts.append(
                f'<text x="{x:.1f}" y="{current_y:.1f}" text-anchor="{anchor}" font-family="Helvetica" font-size="{size_px}" font-weight="{weight}" fill="{fill}">{escape(subline)}</text>'
            )
            current_y += line_gap_px
    return parts


def _line_count(lines: tuple[str, ...]) -> int:
    count = 0
    for line in lines:
        count += len([segment for segment in line.split("\n") if segment])
    return count or 1


def _top_rounded_header_path(
    *, x: float, y: float, width: float, height: float, radius: float
) -> str:
    r = max(0.0, min(radius, width / 2.0, height))
    right = x + width
    bottom = y + height
    return (
        f"M {x + r:.1f} {y:.1f} "
        f"L {right - r:.1f} {y:.1f} "
        f"Q {right:.1f} {y:.1f} {right:.1f} {y + r:.1f} "
        f"L {right:.1f} {bottom:.1f} "
        f"L {x:.1f} {bottom:.1f} "
        f"L {x:.1f} {y + r:.1f} "
        f"Q {x:.1f} {y:.1f} {x + r:.1f} {y:.1f} Z"
    )
