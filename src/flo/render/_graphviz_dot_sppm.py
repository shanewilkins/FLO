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
    theme = resolve_sppm_theme(options.sppm_theme)

    lines: list[str] = ["digraph {"]
    rankdir = "TB" if options.orientation == "tb" else "LR"
    lines.append(f"  rankdir={rankdir};")
    lines.append(
        "  graph [compound=true, newrank=true, nodesep=0.8, ranksep=1.1, splines=true];"
    )
    lines.append("  node [fontname=Helvetica, style=filled];")
    lines.append("  edge [fontname=Helvetica];")

    for node in nodes:
        lines.extend(_render_sppm_node(node, options=options, theme=theme))

    for edge in edges:
        lines.extend(_render_sppm_edge(edge, nodes_by_id=nodes_by_id))

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node rendering
# ---------------------------------------------------------------------------


def _render_sppm_node(node: dict[str, Any], options: RenderOptions, theme: SppmTheme) -> list[str]:
    node_id = str(node.get("id") or "")
    if not node_id:
        return []
    kind = str(node.get("kind") or node.get("type") or "task").lower()
    name = str(node.get("name") or node_id)
    metadata: dict[str, Any] = node.get("metadata") or {}
    workers: list[Any] = node.get("workers") or []
    note = str(node.get("note") or "")

    if kind in ("start", "end"):
        style = theme.start_end
        attrs = [
            f'label="{_escape(name)}"',
            "shape=rect",
            'style="rounded,filled"',
            f'fillcolor="{style.fill}"',
            f'color="{style.border}"',
            "penwidth=1.5",
        ]
        return [f'  "{_escape(node_id)}" [{", ".join(attrs)}];']

    # Task node — HTML table: colored header row + white info sub-row
    value_class_raw = str(metadata.get("value_class") or "")
    try:
        vc = ProcessValueClass(value_class_raw) if value_class_raw else None
    except ValueError:
        vc = None
    style = theme.style_for(vc.value if vc else None)

    html_label = _sppm_html_label(
        name=name,
        metadata=metadata,
        workers=workers,
        style=style,
        note=note,
        options=options,
    )
    return [f'  "{_escape(node_id)}" [shape=none, margin=0, label={html_label}];']


def _sppm_html_label(
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    style: SppmNodeStyle,
    note: str,
    options: RenderOptions,
) -> str:
    """Build a Graphviz HTML-like table label: colored header + white info sub-row."""
    name_html = _html_escape(name)
    header = (
        f'<TR><TD BGCOLOR="{style.fill}" ALIGN="CENTER">'
        f'<FONT FACE="Helvetica" POINT-SIZE="11"><B>{name_html}</B></FONT>'
        f'</TD></TR>'
    )

    info_lines: list[str] = []

    description = str(metadata.get("description") or "")
    if description:
        info_lines.append(_html_escape(description))

    ct = metadata.get("cycle_time")
    if isinstance(ct, dict) and ct.get("value") is not None:
        info_lines.append(f"CT: {ct['value']} {ct.get('unit', 'min')}")

    if workers:
        info_lines.append(f"Workers: {', '.join(_html_escape(str(w)) for w in workers)}")

    wt = metadata.get("wait_time")
    if isinstance(wt, dict) and wt.get("value") is not None and float(wt["value"]) > 0:
        info_lines.append(f"WT: {wt['value']} {wt.get('unit', 'min')} wait")

    if note and getattr(options, "show_notes", False):
        info_lines.append(f"Note: {_html_escape(note)}")

    rows = header
    if info_lines:
        joined = "<BR ALIGN=\"LEFT\"/>".join(info_lines) + "<BR ALIGN=\"LEFT\"/>"
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


# ---------------------------------------------------------------------------
# Edge rendering
# ---------------------------------------------------------------------------


def _render_sppm_edge(
    edge: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    source = str(edge.get("source") or "")
    target = str(edge.get("target") or "")
    if not source or not target:
        return []
    return [f'  "{_escape(source)}" -> "{_escape(target)}";']


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
