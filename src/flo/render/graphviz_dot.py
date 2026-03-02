"""Graphviz DOT renderers for FLO models."""

from __future__ import annotations

from typing import Any, Dict


def render_flowchart_dot(process: Dict[str, Any] | Any) -> str:
    """Render a simple flowchart DOT representation.

    Supports canonical IR objects and dict-based shapes.
    """
    nodes, edges = _extract_nodes_and_edges(process)

    lines: list[str] = ["digraph {"]
    lines.append("  rankdir=LR;")

    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "task")
        label_name = str(node.get("name") or node_id)
        lane = node.get("lane")
        label = _node_label(node_id=node_id, name=label_name, lane=lane)
        shape = _shape_for_kind(kind)
        lines.append(f'  "{_escape(node_id)}" [label="{_escape(label)}", shape={shape}];')

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue
        label = edge.get("outcome") or edge.get("label")
        if label is not None:
            lines.append(
                f'  "{_escape(str(source))}" -> "{_escape(str(target))}" '
                f'[label="{_escape(str(label))}"];'
            )
        else:
            lines.append(f'  "{_escape(str(source))}" -> "{_escape(str(target))}";')

    lines.append("}")
    return "\n".join(lines)


def render_swimlane_dot(process: Dict[str, Any] | Any) -> str:
    """Render a swimlane-style DOT graph.

    v0.1 fallback currently delegates to flowchart rendering.
    """
    return render_flowchart_dot(process)


def _extract_nodes_and_edges(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if process is None:
        return [], []

    if hasattr(process, "nodes") and hasattr(process, "edges"):
        return _extract_from_ir_object(process)

    if isinstance(process, dict):
        return _extract_from_dict(process)

    return [], []


def _extract_from_ir_object(process: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = []
    for node in getattr(process, "nodes", []) or []:
        attrs = getattr(node, "attrs", {}) or {}
        name = attrs.get("name") if isinstance(attrs, dict) else None
        lane = attrs.get("lane") if isinstance(attrs, dict) else None
        nodes.append(
            {
                "id": getattr(node, "id", ""),
                "kind": getattr(node, "type", "task"),
                "name": name,
                "lane": lane,
            }
        )

    edges = []
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


def _extract_from_dict(process: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_raw = process.get("nodes") or []
    edges_raw = process.get("edges") or []
    nodes = [n for n in nodes_raw if isinstance(n, dict)]
    edges = [e for e in edges_raw if isinstance(e, dict)]
    return nodes, edges


def _shape_for_kind(kind: str) -> str:
    norm = (kind or "task").lower()
    if norm == "start":
        return "circle"
    if norm == "end":
        return "doublecircle"
    if norm == "decision":
        return "diamond"
    if norm == "queue":
        return "box"
    return "box"


def _node_label(node_id: str, name: str, lane: Any | None) -> str:
    # Prefer human-friendly names while keeping stable ids visible.
    if name and name != node_id:
        base = f"{name}\\n({node_id})"
    else:
        base = node_id

    if lane:
        return f"{base}\\n[lane: {lane}]"
    return base


def _escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('"', '\\"')
