"""Special-case SPPM node shape renderers."""

from __future__ import annotations

from html import escape as html_escape
from typing import Any

from flo.schema.subprocess_refs import resolve_subprocess_detail_map_reference

from ._autoformat_wrap import WrapPlan
from ._graphviz_dot_common import _escape
from ._sppm_text import format_text_field, normalize_space
from ._sppm_themes import SppmTheme
from .options import RenderOptions

_SPPM_QUEUE_TRIANGLE_WIDTH = 2.1  # inches
_SPPM_QUEUE_TRIANGLE_HEIGHT = (
    3.0  # inches; almost as tall as rendered decision diamonds
)
_SPPM_QUEUE_NAME_MAX_LEN = 14


def render_sppm_queue_triangle(
    *,
    node: dict[str, Any],
    node_id: str,
    name: str,
    options: RenderOptions,
    theme: SppmTheme,
    wrap_plan: WrapPlan,
) -> str:
    """Render a queue marker as an upright fixed-size triangle with a metadata box below."""
    _ = theme
    queue_border = "#E65100"
    queue_label_bg = "#FFB74D"
    wait_time_min = _get_wait_time_minutes(node)
    queue_max_len = _SPPM_QUEUE_NAME_MAX_LEN
    if options.sppm_max_label_step_name is not None:
        queue_max_len = min(queue_max_len, options.sppm_max_label_step_name)
    queue_name = format_text_field(
        normalize_space(name),
        max_len=queue_max_len,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )
    label_lines = [queue_name if queue_name else "Q"]
    if wait_time_min > 0:
        label_lines.append(f"WT: {wait_time_min:g} min")
    queue_label_html = "<BR/>".join(html_escape(line) for line in label_lines)
    queue_label = (
        f'<<TABLE BORDER="1" COLOR="{queue_border}" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">'
        f'<TR><TD BGCOLOR="{queue_label_bg}" COLOR="#000000">{queue_label_html}</TD></TR></TABLE>>'
    )

    attrs = [
        f"label={queue_label}",
        "shape=triangle",
        "orientation=0",
        f"width={_SPPM_QUEUE_TRIANGLE_WIDTH}",
        f"height={_SPPM_QUEUE_TRIANGLE_HEIGHT}",
        "fixedsize=true",
        'style="solid"',
        f'color="{queue_border}"',
        'fontcolor="#000000"',
        "penwidth=1.5",
        "fontsize=13",
        "fontname=Helvetica",
    ]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def render_sppm_subprocess_node(
    *,
    node: dict[str, Any],
    node_id: str,
    name: str,
    options: RenderOptions,
    wrap_plan: WrapPlan,
) -> str:
    """Render subprocesses as dotted oval containers with detail-map metadata below."""
    metadata: dict[str, Any] = node.get("metadata") or {}
    detail_map_ref = resolve_subprocess_detail_map_reference(
        node_id=node_id, metadata=metadata
    )
    name_label = format_text_field(
        normalize_space(name),
        max_len=options.sppm_max_label_step_name,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\\n",
    )
    subprocess_label = f"{name_label}\\nSubprocess\\nDetail map: {detail_map_ref}"
    attrs = [
        f'label="{_escape(subprocess_label)}"',
        "shape=ellipse",
        'style="filled,dotted"',
        'fillcolor="#F8FAFC"',
        'color="#607D8B"',
        "penwidth=1.8",
        "fontsize=11",
        "fontname=Helvetica",
    ]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def _append_chunk_group(*, attrs: list[str], node_id: str, wrap_plan: WrapPlan) -> None:
    display_idx = wrap_plan.node_display_index.get(node_id)
    if wrap_plan.active and display_idx is not None:
        attrs.append(f'group="sppm_col_{display_idx}"')


def _get_wait_time_minutes(node: dict[str, Any]) -> float:
    metadata = node.get("metadata")
    raw = metadata.get("wait_time") if isinstance(metadata, dict) else None
    if isinstance(raw, dict):
        value = raw.get("value")
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0
