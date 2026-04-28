"""SPPM (Standard Process Performance Map) DOT renderer for FLO.

Renders a left-to-right process map with:
  - Nodes color-coded by value_class (VA=green, RNVA=gray, NVA=red)
  - Cycle time shown in node label
  - Workers shown in node label (non-start/end nodes)
  - Wait time shown as edge label on the incoming edge to a step
  - Start/end nodes as rounded rectangles
"""

from __future__ import annotations

from typing import Any

from ._graphviz_dot_common import _escape
from ._autoformat_wrap import append_wrap_layout_hints, build_wrap_plan, WrapPlan
from ._sppm_routing import SppmEdgeRoute, build_sppm_routing_plan
from ._sppm_text import apply_density_filter, abbreviate_workers, format_text_field, normalize_space
from ._sppm_themes import resolve_sppm_theme, SppmTheme, SppmNodeStyle
from .options import RenderOptions
from flo.compiler.ir.enums import ProcessValueClass


def render_sppm_dot(process: dict[str, Any] | Any, options: RenderOptions | None = None) -> str:
    """Render a Standard Process Performance Map (SPPM) as Graphviz DOT."""
    render_options = options or RenderOptions()
    return _render_sppm_graph(process, options=render_options)


def _render_sppm_graph(process: dict[str, Any] | Any, options: RenderOptions) -> str:
    nodes, edges = _extract_sppm_nodes_edges(process)
    nodes_by_id: dict[str, dict[str, Any]] = {
        str(n.get("id", "")): n for n in nodes if n.get("id")
    }
    step_numbering = _build_step_numbering(nodes)
    wrap_plan = build_wrap_plan(nodes, options, planner="placement")
    routing_plan = build_sppm_routing_plan(
        edges=edges,
        options=options,
        step_numbering=step_numbering,
        wrap_plan=wrap_plan,
    )
    theme = resolve_sppm_theme(options.sppm_theme)

    lines: list[str] = ["digraph {"]
    rankdir = _resolve_rankdir(options=options, wrap_active=wrap_plan.active)
    lines.append(f"  rankdir={rankdir};")
    splines = "ortho" if wrap_plan.active else "true"
    nodesep, ranksep = _sppm_graph_spacing(options=options, wrap_active=wrap_plan.active)
    lines.append(
        f"  graph [compound=true, newrank=true, nodesep={nodesep}, ranksep={ranksep}, margin=0.05, pad=0.05, splines={splines}];"
    )
    lines.append("  node [fontname=Helvetica, style=filled];")
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

    lines.append("}")
    return "\n".join(lines)


def _resolve_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    # Wrapped layouts flip rankdir so chunk-local ordering can read naturally:
    # - orientation=lr => rows that read left-to-right, stacked downward
    # - orientation=tb => columns that read top-to-bottom, stepping rightward
    return "TB" if options.orientation == "lr" else "LR"


def _sppm_graph_spacing(*, options: RenderOptions, wrap_active: bool) -> tuple[float, float]:
    if not wrap_active:
        return 0.8, 1.1
    if options.layout_fit == "fit-strict":
        return 0.45, 0.7
    return 0.6, 0.85


# ---------------------------------------------------------------------------
# Node rendering
# ---------------------------------------------------------------------------


def _render_sppm_node(
    node: dict[str, Any],
    options: RenderOptions,
    theme: SppmTheme,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
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

    return [
        _render_sppm_task_node(
            node=node,
            node_id=node_id,
            name=name,
            options=options,
            theme=theme,
            wrap_plan=wrap_plan,
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


def _render_sppm_task_node(
    *,
    node: dict[str, Any],
    node_id: str,
    name: str,
    options: RenderOptions,
    theme: SppmTheme,
    wrap_plan: WrapPlan,
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
    chunk_idx = wrap_plan.node_chunk_index.get(node_id)
    if wrap_plan.active and chunk_idx is not None:
        attrs.append(f'group="sppm_chunk_{chunk_idx}"')


def _sppm_html_label(
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    style: SppmNodeStyle,
    note: str,
    options: RenderOptions,
) -> str:
    """Build a Graphviz HTML-like table label: colored header + white info sub-row."""
    name_text = format_text_field(
        name,
        max_len=options.sppm_max_label_step_name,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )
    name_html = _html_escape_multiline(name_text, break_tag="<BR/>")
    header = (
        f'<TR><TD BGCOLOR="{style.fill}" ALIGN="CENTER">'
        f'<FONT FACE="Helvetica" POINT-SIZE="11"><B>{name_html}</B></FONT>'
        f'</TD></TR>'
    )

    description = normalize_space(str(metadata.get("description") or ""))

    ct = metadata.get("cycle_time")
    ct_line = ""
    if isinstance(ct, dict) and ct.get("value") is not None:
        ct_line = format_text_field(
            f"CT: {ct['value']} {ct.get('unit', 'min')}",
            max_len=options.sppm_max_label_ctwt,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )

    workers_line = ""
    if workers:
        workers_text = ", ".join(str(w) for w in workers)
        if options.sppm_label_density == "compact":
            workers_text = abbreviate_workers([str(w) for w in workers])
        workers_line = format_text_field(
            f"Workers: {workers_text}",
            max_len=options.sppm_max_label_workers,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )

    wt = metadata.get("wait_time")
    wt_line = ""
    if isinstance(wt, dict) and wt.get("value") is not None and float(wt["value"]) > 0:
        wt_line = format_text_field(
            f"WT: {wt['value']} {wt.get('unit', 'min')} wait",
            max_len=options.sppm_max_label_ctwt,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )

    notes_line = ""
    if note and getattr(options, "show_notes", False):
        notes_line = f"Note: {normalize_space(note)}"

    info_lines = apply_density_filter(
        density=options.sppm_label_density,
        description=description,
        ct_line=ct_line,
        wt_line=wt_line,
        workers_line=workers_line,
        notes_line=notes_line,
    )

    rows = header
    if info_lines:
        joined = "<BR ALIGN=\"LEFT\"/>".join(
            _html_escape_multiline(line, break_tag="<BR ALIGN=\"LEFT\"/>") for line in info_lines
        ) + "<BR ALIGN=\"LEFT\"/>"
        rows += (
            f"<HR/>"
            f'<TR><TD BGCOLOR="white" ALIGN="LEFT">'
            f'<FONT FACE="Helvetica" POINT-SIZE="9">{joined}</FONT>'
            f'</TD></TR>'
        )

    return (
        f'<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" '
        f'COLOR="{style.border}">{rows}</TABLE>>'
    )


def _html_escape(text: str) -> str:
    """Escape special HTML characters for Graphviz HTML-like labels."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_escape_multiline(text: str, break_tag: str) -> str:
    return break_tag.join(_html_escape(part) for part in text.split("\n"))


# ---------------------------------------------------------------------------
# Edge rendering
# ---------------------------------------------------------------------------


def _render_sppm_edge(
    edge: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    options: RenderOptions,
    step_numbering: dict[str, int],
    wrap_plan: WrapPlan,
    route: SppmEdgeRoute | None,
) -> list[str]:
    source = str(edge.get("source") or "")
    target = str(edge.get("target") or "")
    if not source or not target:
        return []
    if route is None:
        return []

    lines: list[str] = []
    for corridor_node in route.corridor_nodes:
        lines.append(f'  "{corridor_node.node_id}" [{", ".join(corridor_node.attrs)}];')
    for anchor in route.anchors:
        lines.append(f'  "{anchor.anchor_id}" [{", ".join(anchor.attrs)}];')
    for segment in route.segments:
        lines.append(
            f'  "{_escape(segment.source_id)}" -> "{_escape(segment.target_id)}" '
            f'[{", ".join(_escape_sppm_route_attrs(segment.attrs))}];'
        )
    return lines


def _escape_sppm_route_attrs(attrs: tuple[str, ...]) -> list[str]:
    escaped: list[str] = []
    for attr in attrs:
        if attr.startswith('label="') or attr.startswith('xlabel="'):
            prefix, value = attr.split('="', 1)
            escaped.append(f'{prefix}="{_escape(value[:-1])}"')
            continue
        escaped.append(attr)
    return escaped


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
    process: dict[str, Any] | Any,
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
