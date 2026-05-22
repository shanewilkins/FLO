"""Backend-neutral task-card layout helpers for SPPM nodes."""

from __future__ import annotations

from dataclasses import dataclass

from ._sppm_node_content import SppmNodeContent

_SPPM_TASK_MAX_WIDTH = 220
_SPPM_TASK_MIN_WIDTH = 80
_TASK_PORT_GUTTER_PX = 8
_TASK_HEADER_PADDING_PX = 6
_TASK_BODY_PADDING_PX = 6
_TASK_BODY_TEXT_OFFSET_PX = 4


@dataclass(frozen=True)
class SppmTaskCardLayout:
    """Renderer-neutral layout metrics for an SPPM task card."""

    content_width_px: int
    gutter_width_px: int = _TASK_PORT_GUTTER_PX
    header_padding_px: int = _TASK_HEADER_PADDING_PX
    body_padding_px: int = _TASK_BODY_PADDING_PX
    body_text_offset_px: int = _TASK_BODY_TEXT_OFFSET_PX


def build_sppm_task_card_layout(content: SppmNodeContent) -> SppmTaskCardLayout:
    """Estimate shared task-card geometry from task title and body lines."""
    name_line_count = content.title.count("\n") + 1
    body_line_count = (
        sum(line.count("\n") + 1 for line in content.info_lines)
        if content.info_lines
        else 0
    )
    header_pts = name_line_count * 23
    body_pts = body_line_count * 14 + (12 if body_line_count else 0)
    hr_pts = 1 if body_line_count else 0
    estimated_height = header_pts + body_pts + hr_pts
    content_width = max(
        min(estimated_height, _SPPM_TASK_MAX_WIDTH), _SPPM_TASK_MIN_WIDTH
    )
    return SppmTaskCardLayout(content_width_px=content_width)
