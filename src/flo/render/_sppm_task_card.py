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

    gutter_width_px: int = _TASK_PORT_GUTTER_PX
    header_padding_px: int = _TASK_HEADER_PADDING_PX
    body_padding_px: int = _TASK_BODY_PADDING_PX
    body_text_offset_px: int = _TASK_BODY_TEXT_OFFSET_PX


def build_sppm_task_card_layout(content: SppmNodeContent) -> SppmTaskCardLayout:
    """Return shared task-card spacing tokens used by SVG node rendering."""
    _ = content
    return SppmTaskCardLayout()
