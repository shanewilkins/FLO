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
import textwrap
from typing import Any

from ._graphviz_dot_common import _escape
from ._autoformat_wrap import append_wrap_layout_hints, build_wrap_plan, WrapPlan
from ._sppm_routing import SppmEdgeRoute, SppmRoutingPlan, build_sppm_routing_plan
from ._sppm_text import apply_density_filter, abbreviate_workers, format_text_field, normalize_space
from ._sppm_themes import resolve_sppm_theme, SppmTheme, SppmNodeStyle
from .options import RenderOptions
from flo.compiler.ir.enums import ProcessValueClass


_SPPM_DECISION_MIN_WIDTH = 2.4
_SPPM_DECISION_MIN_HEIGHT = 1.4
_SPPM_NAME_SOFT_WRAP = 24
_SPPM_DESCRIPTION_SOFT_WRAP = 42
_SPPM_WORKERS_SOFT_WRAP = 36
_SPPM_TASK_MIN_WIDTH = 220


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
        nodes=nodes,
        edges=edges,
        options=options,
        step_numbering=step_numbering,
        wrap_plan=wrap_plan,
    )
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


def _build_label_metric_lines(
    metadata: dict[str, Any],
    workers: list[Any],
    note: str,
    options: RenderOptions,
) -> tuple[str, str, str, str, str]:
    """Return ``(description, ct_line, workers_line, wt_line, notes_line)`` formatted strings."""
    description = _soft_wrap_text(
        normalize_space(str(metadata.get("description") or "")),
        width=_SPPM_DESCRIPTION_SOFT_WRAP,
    )

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
        if options.sppm_max_label_workers is None:
            workers_line = _soft_wrap_text(f"Workers: {workers_text}", width=_SPPM_WORKERS_SOFT_WRAP)
        else:
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

    return description, ct_line, workers_line, wt_line, notes_line


def _sppm_html_label(
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    style: SppmNodeStyle,
    note: str,
    options: RenderOptions,
    port_counts: dict[str, int],
) -> str:
    """Build a Graphviz HTML-like table label: colored header + white info sub-row."""
    if options.sppm_max_label_step_name is None:
        name_text = _soft_wrap_text(normalize_space(name), width=_SPPM_NAME_SOFT_WRAP)
    else:
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

    description, ct_line, workers_line, wt_line, notes_line = _build_label_metric_lines(
        metadata, workers, note, options
    )

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

    content_table = (
        f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" BGCOLOR="white">'
        f'{rows}</TABLE>'
    )
    return _wrap_sppm_label_with_ports(
        content_table=content_table,
        port_counts=port_counts,
        border_color=style.border,
        header_fill=style.fill,
    )


def _wrap_sppm_label_with_ports(
    *,
    content_table: str,
    port_counts: dict[str, int],
    border_color: str,
    header_fill: str,
) -> str:
    in_count = max(0, int(port_counts.get("in", 0)))
    out_count = max(0, int(port_counts.get("out", 0)))
    left_stack = _sppm_port_stack_html(role="in", count=in_count)
    return_in_stack = _sppm_port_stack_html(role="rin", count=in_count)
    right_stack = _sppm_port_stack_html(role="out", count=out_count)
    table_prefix = (
        f'<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0" '
        f'COLOR="{border_color}" BGCOLOR="white">'
    )

    if in_count == 0 and out_count == 0:
        return (
            f'{table_prefix}<TR><TD BGCOLOR="{header_fill}"></TD><TD PORT="boundary_in" HEIGHT="1" BGCOLOR="{header_fill}"></TD><TD BGCOLOR="{header_fill}"></TD><TD BGCOLOR="{header_fill}"></TD></TR>'
            f'<TR><TD WIDTH="8"></TD><TD WIDTH="{_SPPM_TASK_MIN_WIDTH}">{content_table}</TD><TD WIDTH="8"></TD><TD WIDTH="8"></TD></TR>'
            f'<TR><TD></TD><TD PORT="boundary_out" HEIGHT="1"></TD><TD></TD><TD></TD></TR></TABLE>>'
        )

    return (
        f'{table_prefix}'
        f'<TR><TD BGCOLOR="{header_fill}"></TD><TD PORT="boundary_in" HEIGHT="1" BGCOLOR="{header_fill}"></TD><TD BGCOLOR="{header_fill}"></TD><TD BGCOLOR="{header_fill}"></TD></TR>'
        f'<TR><TD WIDTH="8">{left_stack}</TD><TD WIDTH="{_SPPM_TASK_MIN_WIDTH}">{content_table}</TD><TD WIDTH="8">{return_in_stack}</TD><TD WIDTH="8">{right_stack}</TD></TR>'
        f'<TR><TD></TD><TD PORT="boundary_out" HEIGHT="1"></TD><TD></TD><TD></TD></TR>'
        f'</TABLE>>'
    )


def _sppm_port_stack_html(*, role: str, count: int) -> str:
    if count <= 0:
        return '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0"><TR><TD WIDTH="8" HEIGHT="12"></TD></TR></TABLE>'

    rows = "".join(
        f'<TR><TD PORT="{role}_{slot}" WIDTH="8" HEIGHT="12"></TD></TR>'
        for slot in range(count)
    )
    return f'<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">{rows}</TABLE>'


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


def _html_escape(text: str) -> str:
    """Escape special HTML characters for Graphviz HTML-like labels."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_escape_multiline(text: str, break_tag: str) -> str:
    return break_tag.join(_html_escape(part) for part in text.split("\n"))


def _soft_wrap_text(text: str, *, width: int) -> str:
    if not text or width < 2:
        return text
    wrapped = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    return "\n".join(wrapped) if wrapped else text


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
        source_endpoint, target_endpoint, rendered_attrs = _materialize_sppm_segment(segment)
        lines.append(
            f'  {source_endpoint} -> {target_endpoint} '
            f'[{", ".join(_escape_sppm_route_attrs(rendered_attrs))}];'
        )
    return lines


def _materialize_sppm_segment(segment: Any) -> tuple[str, str, tuple[str, ...]]:
    source_endpoint = f'"{_escape(segment.source_id)}"'
    target_endpoint = f'"{_escape(segment.target_id)}"'
    remaining_attrs: list[str] = []

    for attr in segment.attrs:
        if attr.startswith("tailport="):
            source_endpoint = _apply_port_attr_to_endpoint(source_endpoint, attr)
            continue
        if attr.startswith("headport="):
            target_endpoint = _apply_port_attr_to_endpoint(target_endpoint, attr)
            continue
        remaining_attrs.append(attr)

    return source_endpoint, target_endpoint, tuple(remaining_attrs)


def _apply_port_attr_to_endpoint(endpoint: str, attr: str) -> str:
    _, raw_value = attr.split("=", 1)
    value = raw_value.strip().strip('"')
    if ":" not in value:
        return f"{endpoint}:{value}"

    port_name, compass = value.split(":", 1)
    return f'{endpoint}:"{_escape(port_name)}":{compass}'


def _render_sppm_spine_constraints(
    *,
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> list[str]:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        if (source, target) in seen:
            continue
        route = routing_plan.route_for(source, target)
        if route is None or route.is_rework:
            continue
        seen.add((source, target))
        lines.append(
            f'  "{_escape(source)}" -> "{_escape(target)}" [style=invis, constraint=true, weight=24];'
        )
    return lines


def _rework_target_ids(edges: list[dict[str, Any]], routing_plan: SppmRoutingPlan) -> set[str]:
    """Return the set of node IDs that are targets of any rework edge."""
    result: set[str] = set()
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        route = routing_plan.route_for(source, target)
        if route is not None and route.is_rework:
            result.add(target)
    return result


def _collect_rework_pairs(
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """Classify rework edges into branch, return, and alignment pairs.

    Returns ``(rework_pairs, branch_anchor_pairs, return_anchor_pairs)`` where
    each element is a list of ``(node_id, anchor_id)`` or ``(source, target)``
    tuples used to emit rank/chain constraints.
    """
    all_rework_targets = _rework_target_ids(edges, routing_plan)
    rework_pairs: list[tuple[str, str]] = []
    branch_anchor_pairs: list[tuple[str, str]] = []
    return_anchor_pairs: list[tuple[str, str]] = []
    seen_targets: set[str] = set()

    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            continue
        route = routing_plan.route_for(source, target)
        if route is None or not route.is_rework:
            continue
        anchor_id = route.anchors[0].anchor_id if route.anchors else ""
        if source in all_rework_targets:
            if anchor_id:
                return_anchor_pairs.append((target, anchor_id))
            continue
        if target in seen_targets:
            continue
        seen_targets.add(target)
        rework_pairs.append((source, target))
        if anchor_id:
            branch_anchor_pairs.append((target, anchor_id))

    return rework_pairs, branch_anchor_pairs, return_anchor_pairs


def _render_sppm_secondary_line_constraints(
    *,
    edges: list[dict[str, Any]],
    routing_plan: SppmRoutingPlan,
) -> list[str]:
    """Emit invisible constraints for a stable secondary (rework) line.

    - Align each rework target with its local rework source column.
    - Chain rework targets left-to-right so they form a coherent lower lane.
    """
    rework_pairs, branch_anchor_pairs, return_anchor_pairs = _collect_rework_pairs(edges, routing_plan)

    if not rework_pairs:
        return []

    lines: list[str] = []

    # Column-align each rework task with its branch source in LR layout.
    # rank=same forces the same horizontal column, so the rework node lands
    # directly below the decision that spawned it.  The return edge then
    # travels leftward (west→east) to re-enter the mainline, producing the
    # right-to-left secondary flow.
    for idx, (source, target) in enumerate(rework_pairs):
        lines.append(f"  subgraph sppm_secondary_rank_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(source)}";')
        lines.append(f'    "{_escape(target)}";')
        lines.append("  }")

    # Keep the secondary line ordered and compact.
    ordered_targets = [target for _, target in rework_pairs]
    for left, right in zip(ordered_targets, ordered_targets[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=true, weight=16, minlen=1];'
        )

    # Shared branch-out track: align and chain branch anchors so branch loops
    # do not freely criss-cross across the secondary line.
    for idx, (target, anchor_id) in enumerate(branch_anchor_pairs):
        lines.append(f"  subgraph sppm_secondary_branch_track_{idx} {{")
        lines.append("    rank=same;")
        lines.append(f'    "{_escape(target)}";')
        lines.append(f'    "{_escape(anchor_id)}";')
        lines.append("  }")
    ordered_branch_anchors = [anchor_id for _, anchor_id in branch_anchor_pairs]
    for left, right in zip(ordered_branch_anchors, ordered_branch_anchors[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=false, weight=0, minlen=1];'
        )

    # Return anchors: position is pinned in a two-pass render (see graphviz service).
    # Omit rank=same so Graphviz does not pull anchors to an intermediate Y between
    # the rework node and its mainline target.  The chain (invis edges) is retained to
    # keep anchors in left-to-right order without adding rank constraints.
    ordered_return_anchors = [anchor_id for _, anchor_id in return_anchor_pairs]
    for left, right in zip(ordered_return_anchors, ordered_return_anchors[1:]):
        lines.append(
            f'  "{_escape(left)}" -> "{_escape(right)}" [style=invis, constraint=false, weight=0, minlen=1];'
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
