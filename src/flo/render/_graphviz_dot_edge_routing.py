"""Shared DOT edge-routing helpers for flowchart and swimlane renderers."""

from __future__ import annotations

from typing import Any

from .options import RenderOptions


def _append_edges(
    lines: list[str],
    edges: list[dict[str, Any]],
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
    boundary_edges: set[tuple[str, str]] | None = None,
    node_sequence_index: dict[str, int] | None = None,
    wrap_active: bool = False,
) -> None:
    """Append DOT edge lines, including shared boundary and rework routing."""
    for edge_index, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        source_id = str(source)
        target_id = str(target)
        is_boundary = (source_id, target_id) in (boundary_edges or set())

        if _is_rework_edge(
            edge=edge,
            source=source_id,
            target=target_id,
            node_sequence_index=node_sequence_index or {},
        ):
            _append_rework_corridor_edge(
                lines=lines,
                edge=edge,
                edge_index=edge_index,
                source=source_id,
                target=target_id,
                options=options,
                use_swimlanes=use_swimlanes,
                node_lanes=node_lanes,
                boundary_edges=boundary_edges or set(),
                node_sequence_index=node_sequence_index or {},
                wrap_active=wrap_active,
            )
            continue

        if is_boundary:
            _append_boundary_corridor_edge(
                lines=lines,
                edge=edge,
                edge_index=edge_index,
                source=source_id,
                target=target_id,
                options=options,
                use_swimlanes=use_swimlanes,
                node_lanes=node_lanes,
                boundary_edges=boundary_edges or set(),
                node_sequence_index=node_sequence_index or {},
                wrap_active=wrap_active,
            )
            continue

        edge_attrs = _edge_attrs(
            edge=edge,
            source=source_id,
            target=target_id,
            options=options,
            use_swimlanes=use_swimlanes,
            node_lanes=node_lanes,
            boundary_edges=boundary_edges or set(),
            node_sequence_index=node_sequence_index or {},
        )
        lines.append(
            f'  "{_escape(source_id)}" -> "{_escape(target_id)}" '
            f'[{", ".join(edge_attrs)}];'
        )


def _append_boundary_corridor_edge(
    *,
    lines: list[str],
    edge: dict[str, Any],
    edge_index: int,
    source: str,
    target: str,
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
    boundary_edges: set[tuple[str, str]],
    node_sequence_index: dict[str, int],
    wrap_active: bool,
) -> None:
    anchor_id = _boundary_anchor_id(source=source, target=target, edge_index=edge_index)
    lines.append(
        f'  "{anchor_id}" [shape=point, width=0.01, height=0.01, label="", style=invis];'
    )

    base_segment_attrs = _edge_attrs(
        edge=edge,
        source=source,
        target=target,
        options=options,
        use_swimlanes=use_swimlanes,
        node_lanes=node_lanes,
        boundary_edges=boundary_edges,
        node_sequence_index=node_sequence_index,
    )
    source_port, target_port = _corridor_ports(options=options, wrap_active=wrap_active)
    second_segment_attrs = [target_port, *base_segment_attrs]
    first_segment_attrs = [
        source_port,
        *_without_boundary_span_attrs(_without_edge_label(base_segment_attrs)),
    ]
    _append_unique_attr(first_segment_attrs, "constraint=false")
    _append_unique_attr(first_segment_attrs, "weight=0")
    _append_unique_attr(first_segment_attrs, "arrowhead=none")

    lines.append(
        f'  "{_escape(source)}" -> "{anchor_id}" '
        f'[{", ".join(first_segment_attrs)}];'
    )
    lines.append(
        f'  "{anchor_id}" -> "{_escape(target)}" '
        f'[{", ".join(second_segment_attrs)}];'
    )


def _append_rework_corridor_edge(
    *,
    lines: list[str],
    edge: dict[str, Any],
    edge_index: int,
    source: str,
    target: str,
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
    boundary_edges: set[tuple[str, str]],
    node_sequence_index: dict[str, int],
    wrap_active: bool,
) -> None:
    anchor_id = _rework_anchor_id(source=source, target=target, edge_index=edge_index)
    lines.append(
        f'  "{anchor_id}" [shape=point, width=0.01, height=0.01, label="", style=invis];'
    )

    base_segment_attrs = _edge_attrs(
        edge=edge,
        source=source,
        target=target,
        options=options,
        use_swimlanes=use_swimlanes,
        node_lanes=node_lanes,
        boundary_edges=boundary_edges,
        node_sequence_index=node_sequence_index,
    )
    source_port, target_port = _corridor_ports(options=options, wrap_active=wrap_active)
    second_segment_attrs = [target_port, *base_segment_attrs]
    first_segment_attrs = [
        source_port,
        *_without_boundary_span_attrs(_without_edge_label(base_segment_attrs)),
    ]
    _append_unique_attr(first_segment_attrs, "constraint=false")
    _append_unique_attr(first_segment_attrs, "weight=0")
    _append_unique_attr(first_segment_attrs, "arrowhead=none")

    lines.append(
        f'  "{_escape(source)}" -> "{anchor_id}" '
        f'[{", ".join(first_segment_attrs)}];'
    )
    lines.append(
        f'  "{anchor_id}" -> "{_escape(target)}" '
        f'[{", ".join(second_segment_attrs)}];'
    )


def _without_edge_label(edge_attrs: list[str]) -> list[str]:
    return [attr for attr in edge_attrs if not attr.startswith("label=")]


def _without_boundary_span_attrs(edge_attrs: list[str]) -> list[str]:
    return [attr for attr in edge_attrs if not attr.startswith("minlen=") and not attr.startswith("penwidth=")]


def _append_unique_attr(attrs: list[str], value: str) -> None:
    if value not in attrs:
        attrs.append(value)


def _corridor_ports(*, options: RenderOptions, wrap_active: bool) -> tuple[str, str]:
    rankdir = _resolve_effective_rankdir(options=options, wrap_active=wrap_active)
    if rankdir == "TB":
        return ("tailport=s", "headport=n")
    return ("tailport=e", "headport=w")


def _resolve_effective_rankdir(*, options: RenderOptions, wrap_active: bool) -> str:
    if not wrap_active:
        return "TB" if options.orientation == "tb" else "LR"
    return "TB" if options.orientation == "lr" else "LR"


def _rework_anchor_id(*, source: str, target: str, edge_index: int) -> str:
    source_part = _safe_edge_id_part(source)
    target_part = _safe_edge_id_part(target)
    return f'__rework_corridor_{source_part}_{target_part}_{edge_index}'


def _boundary_anchor_id(*, source: str, target: str, edge_index: int) -> str:
    source_part = _safe_edge_id_part(source)
    target_part = _safe_edge_id_part(target)
    return f'__boundary_corridor_{source_part}_{target_part}_{edge_index}'


def _safe_edge_id_part(value: str) -> str:
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned) or "edge"


def _edge_attrs(
    edge: dict[str, Any],
    source: str,
    target: str,
    options: RenderOptions,
    use_swimlanes: bool,
    node_lanes: dict[str, str],
    boundary_edges: set[tuple[str, str]],
    node_sequence_index: dict[str, int],
) -> list[str]:
    edge_attrs: list[str] = []
    is_rework = _is_rework_edge(
        edge=edge,
        source=source,
        target=target,
        node_sequence_index=node_sequence_index,
    )

    if use_swimlanes and _is_cross_lane_edge(source, target, node_lanes):
        edge_attrs.append("constraint=false")

    if (source, target) in boundary_edges:
        edge_attrs.append("minlen=2")
        edge_attrs.append("penwidth=1.2")

    if is_rework:
        if "constraint=false" not in edge_attrs:
            edge_attrs.append("constraint=false")
        edge_attrs.append("minlen=3")
        edge_attrs.append("weight=0")
        edge_attrs.append("style=dashed")

    if options.detail != "summary":
        branch_label = edge.get("outcome") or edge.get("label")
        if branch_label is not None:
            edge_attrs.append(f'label="{_escape(str(branch_label))}"')

    return edge_attrs


def _is_cross_lane_edge(source: str, target: str, node_lanes: dict[str, str]) -> bool:
    source_lane = node_lanes.get(source, "")
    target_lane = node_lanes.get(target, "")
    if not source_lane or not target_lane:
        return False
    return source_lane != target_lane


def _is_rework_edge(
    *,
    edge: dict[str, Any],
    source: str,
    target: str,
    node_sequence_index: dict[str, int],
) -> bool:
    explicit = edge.get("rework")
    if explicit is not None:
        return bool(explicit)

    if str(edge.get("edge_type") or "").strip().lower() == "rework":
        return True

    src_idx = node_sequence_index.get(source)
    dst_idx = node_sequence_index.get(target)
    if src_idx is None or dst_idx is None:
        return False
    return src_idx > dst_idx


def _escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')