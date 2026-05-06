"""Header and footer band rendering for SPPM DOT output.

The publication model decides whether bands exist; this module only turns band
content into Graphviz label structures and anchor edges.
"""

from __future__ import annotations

from typing import Any

from ._graphviz_dot_common import _escape
from ._sppm_render_data import SppmRenderEdge, SppmRenderNode
from ._sppm_text import normalize_space

__all__ = ["build_sppm_header", "render_sppm_footer_band"]


def build_sppm_header(*, publication: Any) -> str:
    """Return the graph-level header label for the primary SPPM page."""
    primary_page = publication.primary_series().pages[0]
    header_band = primary_page.band("header")
    if header_band is None:
        return ""

    header_content = header_band.content
    title_text = normalize_space(header_content.title)
    if not title_text:
        return ""

    metadata_cells = "".join(
        f'<TD ALIGN="LEFT"><FONT FACE="Helvetica" POINT-SIZE="9"><B>{_escape(label)}:</B> {_escape(value)}</FONT></TD>'
        for label, value in header_content.rows
    )
    metadata_row = f"<TR>{metadata_cells}</TR>" if metadata_cells else ""

    return (
        '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" COLOR="#B0BEC5" BGCOLOR="#FAFAFA">'
        f'<TR><TD ALIGN="LEFT"><FONT FACE="Helvetica" POINT-SIZE="16"><B>{_escape(title_text)}</B></FONT></TD></TR>'
        f"{metadata_row}"
        "</TABLE>>"
    )


def render_sppm_footer_band(*, publication: Any, nodes: list[SppmRenderNode], edges: list[SppmRenderEdge]) -> list[str]:
    """Return DOT lines for the optional footer band and its anchor edges."""
    primary_page = publication.primary_series().pages[0]
    footer_band = primary_page.band("footer")
    if footer_band is None:
        return []
    if not footer_band.content.rows and not footer_band.content.notes:
        return []

    footer_id = "__sppm_footer_band"
    footer_label = _build_sppm_footer_label(footer_band.content.rows, footer_band.content.notes)
    lines = [
        "  {",
        "    rank=sink;",
        f'    "{footer_id}" [shape=none, margin=0, label={footer_label}];',
        "  }",
    ]
    for source_id in _footer_anchor_sources(nodes=nodes, edges=edges):
        lines.append(f'  "{_escape(source_id)}" -> "{footer_id}" [style=invis, weight=2, minlen=1];')
    return lines


def _build_sppm_footer_label(rows: tuple[tuple[str, str], ...], notes: tuple[str, ...]) -> str:
    table_rows = "".join(
        f'<TR><TD ALIGN="LEFT"><FONT FACE="Helvetica" POINT-SIZE="9"><B>{_escape(label)}:</B> {_escape(value)}</FONT></TD></TR>'
        for label, value in rows
    )
    note_lines = "<BR ALIGN=\"LEFT\"/>".join(_escape(note) for note in notes)
    notes_row = ""
    if note_lines:
        notes_row = f'<TR><TD ALIGN="LEFT"><FONT FACE="Helvetica" POINT-SIZE="9">{note_lines}</FONT></TD></TR>'
    return (
        '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" COLOR="#CFD8DC" BGCOLOR="#FAFAFA">'
        f"{table_rows}"
        f"{notes_row}"
        "</TABLE>>"
    )


def _footer_anchor_sources(*, nodes: list[SppmRenderNode], edges: list[SppmRenderEdge]) -> list[str]:
    candidates = _footer_end_nodes(nodes)
    if candidates:
        return candidates

    terminal_nodes = _footer_terminal_nodes(nodes=nodes, edges=edges)
    if terminal_nodes:
        return terminal_nodes

    fallback = _footer_fallback_node_id(nodes)
    return [fallback] if fallback else []


def _footer_end_nodes(nodes: list[SppmRenderNode]) -> list[str]:
    return [node_id for node_id in (_node_id(node) for node in nodes) if node_id and _node_kind(nodes, node_id) == "end"]


def _footer_terminal_nodes(*, nodes: list[SppmRenderNode], edges: list[SppmRenderEdge]) -> list[str]:
    outgoing = _edge_source_ids(edges)
    return [node_id for node_id in (_node_id(node) for node in nodes) if node_id and node_id not in outgoing]


def _footer_fallback_node_id(nodes: list[SppmRenderNode]) -> str:
    if not nodes:
        return ""
    return _node_id(nodes[-1])


def _edge_source_ids(edges: list[SppmRenderEdge]) -> set[str]:
    source_ids: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if source and target:
            source_ids.add(source)
    return source_ids


def _node_id(node: SppmRenderNode) -> str:
    return str(node.get("id") or "").strip()


def _node_kind(nodes: list[SppmRenderNode], node_id: str) -> str:
    for node in nodes:
        if _node_id(node) != node_id:
            continue
        return str(node.get("kind") or node.get("type") or "").strip().lower()
    return ""