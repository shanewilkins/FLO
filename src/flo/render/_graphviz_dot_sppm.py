"""SPPM (Standard Process Performance Map) DOT renderer for FLO.

Renders a left-to-right process map with:
  - Nodes color-coded by value_class (VA=green, RNVA=gray, NVA=red)
  - Cycle time shown in node label
  - Workers shown in node label (non-start/end nodes)
  - Wait time shown as edge label on the incoming edge to a step
    - Start/end nodes as rounded rectangles
    - Decision nodes as diamonds
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from ._graphviz_dot_common import _escape
from ._autoformat_wrap import append_wrap_layout_hints, build_wrap_plan, WrapPlan
from ._sppm_edge_render import _render_sppm_edge, _render_sppm_spine_constraints, _render_sppm_secondary_line_constraints
from ._sppm_label_html import _sppm_html_label
from ._sppm_routing import build_sppm_routing_plan
from ._sppm_themes import resolve_sppm_theme, SppmTheme, SppmNodeStyle
from .options import RenderOptions
from flo.compiler.ir.enums import ProcessValueClass

if TYPE_CHECKING:
    from flo.compiler.ir.models import IR
    from ._sppm_postprocess_contract import SppmSvgPostprocessContract


_SPPM_DECISION_MIN_WIDTH = 2.4
_SPPM_DECISION_MIN_HEIGHT = 1.4


def render_sppm_dot(process: IR | dict[str, Any], options: RenderOptions | None = None) -> str:
    """Render a Standard Process Performance Map (SPPM) as Graphviz DOT."""
    render_options = options or RenderOptions()
    dot, _contract = _render_sppm_graph(process, options=render_options)
    return dot


def _render_sppm_graph(process: IR | dict[str, Any], options: RenderOptions) -> tuple[str, SppmSvgPostprocessContract]:
    nodes, edges = _extract_sppm_nodes_edges(process)
    nodes_by_id: dict[str, dict[str, Any]] = {
        str(n.get("id", "")): n for n in nodes if n.get("id")
    }
    step_numbering = _build_step_numbering(nodes)
    wrap_plan = build_wrap_plan(nodes, options, planner="placement")
    routing_plan = build_sppm_routing_plan(
        nodes=nodes,
        edges=edges,
        options=options,
        step_numbering=step_numbering,
        wrap_plan=wrap_plan,
    )
    contract = routing_plan.svg_postprocess_contract
    port_counts = _port_counts_by_node(routing_plan)
    theme = resolve_sppm_theme(options.sppm_theme)

    lines: list[str] = ["digraph {"]
    rankdir = _resolve_rankdir(options=options, wrap_active=wrap_plan.active)
    lines.append(f"  rankdir={rankdir};")
    splines = "ortho"
    nodesep, ranksep = _sppm_graph_spacing(options=options, wrap_active=wrap_plan.active)
    lines.append(
        f"  graph [compound=true, newrank=true, nodesep={nodesep}, ranksep={ranksep}, margin=0.05, pad=0.05, splines={splines}, bgcolor=white];"
    )
    lines.append("  node [fontname=Helvetica];")
    lines.append("  edge [fontname=Helvetica];")

    append_wrap_layout_hints(lines=lines, options=options, plan=wrap_plan)

    for node in nodes:
        lines.extend(
            _render_sppm_node(
                node,
                options=options,
                theme=theme,
                step_numbering=step_numbering,
                wrap_plan=wrap_plan,
                port_counts=port_counts.get(str(node.get("id") or ""), {}),
            )
        )

    for edge in edges:
        lines.extend(
            _render_sppm_edge(
                edge,
                nodes_by_id=nodes_by_id,
                options=options,
                step_numbering=step_numbering,
                wrap_plan=wrap_plan,
                route=routing_plan.route_for(
                    str(edge.get("source") or ""),
                    str(edge.get("target") or ""),
                ),
            )
        )

    # Phase 3: reinforce the primary (non-rework) flow with invisible, high-weight
    # constraints so spacing follows the process spine rather than branch geometry.
    lines.extend(_render_sppm_spine_constraints(edges=edges, routing_plan=routing_plan))
    lines.extend(_render_sppm_secondary_line_constraints(edges=edges, routing_plan=routing_plan))

    lines.append("}")
    return "\n".join(lines), contract


def _resolve_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    # Wrapped layouts flip rankdir so chunk-local ordering can read naturally:
    # - orientation=lr => rows that read left-to-right, stacked downward
    # - orientation=tb => columns that read top-to-bottom, stepping rightward
    return "TB" if options.orientation == "lr" else "LR"


def _sppm_graph_spacing(*, options: RenderOptions, wrap_active: bool) -> tuple[float, float]:
    if not wrap_active:
        if options.layout_spacing == "compact":
            return 0.75, 1.0
        return 0.9, 1.2
    if options.layout_fit == "fit-strict":
        if options.layout_spacing == "compact":
            return 0.25, 0.3
        return 0.3, 0.35
    if options.layout_spacing == "compact":
        return 0.35, 0.3
    return 0.4, 0.35


# ---------------------------------------------------------------------------
# Node rendering
# ---------------------------------------------------------------------------


def _render_sppm_node(
    node: dict[str, Any],
    options: RenderOptions,
    theme: SppmTheme,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    port_counts: dict[str, int],
) -> list[str]:
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
    attrs = [
        f'label="{_escape(name)}"',
        "shape=diamond",
        "regular=true",
        f"width={_SPPM_DECISION_MIN_WIDTH}",
        f"height={_SPPM_DECISION_MIN_HEIGHT}",
        'style="filled"',
        f'fillcolor="{theme.start_end.fill}"',
        f'color="{theme.start_end.border}"',
        "penwidth=1.5",
    ]
    _append_chunk_group(attrs=attrs, node_id=node_id, wrap_plan=wrap_plan)
    return f'  "{_escape(node_id)}" [{", ".join(attrs)}];'


def _render_sppm_task_node(
    *,
    node: dict[str, Any],
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
    value_class_raw = str(metadata.get("value_class") or "")
    try:
        vc = ProcessValueClass(value_class_raw) if value_class_raw else None
    except ValueError:
        vc = None
    return theme.style_for(vc.value if vc else None)


def _append_chunk_group(*, attrs: list[str], node_id: str, wrap_plan: WrapPlan) -> None:
    display_idx = wrap_plan.node_display_index.get(node_id)
    if wrap_plan.active and display_idx is not None:
        attrs.append(f'group="sppm_col_{display_idx}"')


def _port_counts_by_node(routing_plan: Any) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"in": 0, "out": 0})
    for route in routing_plan.route_plan.routes.values():
        counts[route.source_port.node_id]["out"] = max(
            counts[route.source_port.node_id]["out"], route.source_port.slot_index + 1
        )
        counts[route.target_port.node_id]["in"] = max(
            counts[route.target_port.node_id]["in"], route.target_port.slot_index + 1
        )
    return dict(counts)



def _build_step_numbering(nodes: list[dict[str, Any]]) -> dict[str, int]:
    numbering: dict[str, int] = {}
    sequence = 1
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "task").lower()
        if kind in {"start", "end"}:
            continue
        numbering[node_id] = sequence
        sequence += 1
    return numbering


# ---------------------------------------------------------------------------
# Data extraction (handles both IR objects and dict-based inputs)
# ---------------------------------------------------------------------------


def _extract_sppm_nodes_edges(
    process: IR | dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if process is None:
        return [], []
    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_sppm_from_ir(process)
    if isinstance(process, dict):
        return _extract_sppm_from_dict(process)
    return [], []


def _extract_sppm_from_ir(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    for node in getattr(process, "nodes", []) or []:
        attrs: dict[str, Any] = (getattr(node, "attrs", None) or {}) if hasattr(node, "attrs") else {}
        raw_metadata = attrs.get("metadata") if isinstance(attrs, dict) else None
        raw_workers = attrs.get("workers") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": attrs.get("name") if isinstance(attrs, dict) else None,
                "note": attrs.get("note") if isinstance(attrs, dict) else None,
                "metadata": raw_metadata if isinstance(raw_metadata, dict) else {},
                "workers": raw_workers if isinstance(raw_workers, list) else [],
            }
        )

    edges: list[dict[str, Any]] = []
    for edge in getattr(process, "edges", []) or []:
        edges.append(
            {
                "source": getattr(edge, "source", None),
                "target": getattr(edge, "target", None),
                "outcome": getattr(edge, "outcome", None),
                "label": getattr(edge, "label", None),
                "edge_type": getattr(edge, "edge_type", None),
                "rework": getattr(edge, "rework", None),
            }
        )
    return nodes, edges


def _extract_sppm_from_dict(
    process: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_raw = process.get("nodes") or []
    edges_raw = process.get("edges") or []

    nodes: list[dict[str, Any]] = []
    for node in nodes_raw:
        if not isinstance(node, dict):
            continue
        # metadata may live at top-level or nested under attrs
        raw_metadata = node.get("metadata")
        if not isinstance(raw_metadata, dict):
            nested_attrs = node.get("attrs")
            raw_metadata = nested_attrs.get("metadata") if isinstance(nested_attrs, dict) else None
        raw_workers = node.get("workers")
        if not isinstance(raw_workers, list):
            nested_attrs = node.get("attrs")
            raw_workers = nested_attrs.get("workers") if isinstance(nested_attrs, dict) else None
        nodes.append(
            {
                "id": node.get("id"),
                "kind": node.get("kind") or node.get("type") or "task",
                "name": node.get("name"),
                "note": node.get("note"),
                "metadata": raw_metadata if isinstance(raw_metadata, dict) else {},
                "workers": raw_workers if isinstance(raw_workers, list) else [],
            }
        )

    edges = [e for e in edges_raw if isinstance(e, dict)]
    return nodes, edges
