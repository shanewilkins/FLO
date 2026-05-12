"""Node rendering primitives for SPPM DOT output.

This module owns only node-level presentation concerns. Graph assembly,
publication bands, and input normalization live elsewhere so the renderer can
evolve per concern instead of by growing one hotspot file.
"""

from __future__ import annotations

from typing import Any

from flo.compiler.ir.enums import ProcessValueClass

from ._autoformat_wrap import WrapPlan
from ._sppm_metadata_schema import (
    get_metadata_value_class,
)
from ._graphviz_dot_common import _escape
from ._sppm_label_html import _sppm_html_label
from ._sppm_render_data import SppmRenderNode
from ._sppm_special_node_shapes import render_sppm_queue_triangle, render_sppm_subprocess_node
from ._sppm_themes import SppmNodeStyle, SppmTheme
from .options import RenderOptions

_SPPM_DECISION_MIN_WIDTH = 1.64
_SPPM_DECISION_MIN_HEIGHT = 0.94
_SPPM_DEFAULT_BOX_HEIGHT = 1.2  # inches

__all__ = ["render_sppm_node"]


def render_sppm_node(
    node: SppmRenderNode,
    *,
    options: RenderOptions,
    theme: SppmTheme,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    port_counts: dict[str, int],
) -> list[str]:
    """Render one normalized SPPM node to DOT lines."""
    node_id = str(node.get("id") or "")
    if not node_id:
        return []

    kind = str(node.get("kind") or node.get("type") or "task").lower()
    name = str(node.get("name") or node_id)
    if options.sppm_step_numbering == "node" and node_id in step_numbering:
        name = f"{step_numbering[node_id]}. {name}"

    if kind in ("start", "end"):
        return [_render_sppm_start_end_node(node_id=node_id, name=name, theme=theme, wrap_plan=wrap_plan)]
    if kind == "decision":
        return [_render_sppm_decision_node(node_id=node_id, name=name, theme=theme, wrap_plan=wrap_plan)]
    if kind == "queue":
        return [render_sppm_queue_triangle(node=node, node_id=node_id, name=name, theme=theme, wrap_plan=wrap_plan)]
    if kind == "subprocess":
        return [render_sppm_subprocess_node(node=node, node_id=node_id, name=name, wrap_plan=wrap_plan)]

    return [
        _render_sppm_task_node(
            node=node,
            node_id=node_id,
            name=name,
            options=options,
            theme=theme,
            wrap_plan=wrap_plan,
            port_counts=port_counts,
        )
    ]


def _render_sppm_start_end_node(*, node_id: str, name: str, theme: SppmTheme, wrap_plan: WrapPlan) -> str:
    style = theme.start_end
    attrs = [
        f'label="{_escape(name)}"',
        "shape=rect",
        'style="rounded,filled"',
        f'fillcolor="{style.fill}"',
        f'color="{style.border}"',
        "penwidth=1.5",
    ]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def _render_sppm_decision_node(*, node_id: str, name: str, theme: SppmTheme, wrap_plan: WrapPlan) -> str:
    label = name
    attrs = [
        f'label="{_escape(label)}"',
        "shape=diamond",
        "regular=true",
        f"width={_SPPM_DECISION_MIN_WIDTH}",
        f"height={_SPPM_DECISION_MIN_HEIGHT}",
        'style="filled"',
        f'fillcolor="{theme.decision.fill}"',
        f'color="{theme.decision.border}"',
        "penwidth=1.5",
    ]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def _render_sppm_task_node(
    *,
    node: SppmRenderNode,
    node_id: str,
    name: str,
    options: RenderOptions,
    theme: SppmTheme,
    wrap_plan: WrapPlan,
    port_counts: dict[str, int],
) -> str:
    metadata: dict[str, Any] = node.get("metadata") or {}
    workers: list[Any] = node.get("workers") or []
    note = str(node.get("note") or "")
    style = _resolve_sppm_value_style(metadata=metadata, theme=theme)
    html_label = _sppm_html_label(
        node_id=node_id,
        kind=str(node.get("kind") or node.get("type") or "task").lower(),
        name=name,
        metadata=metadata,
        workers=workers,
        style=style,
        note=note,
        options=options,
        port_counts=port_counts,
    )
    attrs = ["shape=none", "margin=0", f"label={html_label}"]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def _resolve_sppm_value_style(*, metadata: dict[str, Any], theme: SppmTheme) -> SppmNodeStyle:
    value_class_raw = get_metadata_value_class(metadata)
    try:
        value_class = ProcessValueClass(value_class_raw) if value_class_raw else None
    except ValueError:
        value_class = None
    return theme.style_for(value_class.value if value_class else None)


def _append_chunk_group(*, attrs: list[str], node_id: str, wrap_plan: WrapPlan) -> None:
    display_idx = wrap_plan.node_display_index.get(node_id)
    if wrap_plan.active and display_idx is not None:
        attrs.append(f'group="sppm_col_{display_idx}"')