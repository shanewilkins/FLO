"""Orientation-aware wrap planning shared across DOT renderers.

API convention (v0.1): expose one public planner entrypoint,
`build_wrap_plan(...)`, and keep strategy implementations private.
Renderers choose strategy via an explicit `planner=` value instead of importing
multiple public builder functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Any, Literal

from .layout_core import NodeMeasure, PlacementConstraints, PlacementPlan, build_placement_plan
from .options import RenderOptions
from ._sppm_text import apply_density_filter, abbreviate_workers, format_text_field, normalize_space

_DEFAULT_NODE_WIDTH_PX = 220
_DEFAULT_NODE_HEIGHT_PX = 80
_PREFERRED_MIN_CHUNK_SIZE = 3
_STRICT_MIN_CHUNK_SIZE = 2
_HORIZONTAL_GAP_PX = 48
_VERTICAL_GAP_PX = 60
_PREFERRED_MARGIN_PX = 48
_STRICT_MARGIN_PX = 180


WrapPlannerKind = Literal["chunked", "placement"]


@dataclass(frozen=True)
class WrapPlan:
    """Deterministic wrap plan for sequence-oriented layout."""

    active: bool
    chunk_size: int
    chunks: list[list[str]]
    display_chunks: list[list[str]]
    boundary_edges: set[tuple[str, str]]
    node_chunk_index: dict[str, int]
    placement_plan: PlacementPlan | None


def build_wrap_plan(
    nodes: list[dict[str, Any]],
    options: RenderOptions,
    *,
    planner: WrapPlannerKind,
) -> WrapPlan:
    """Build wrap planning data for renderers.

    Args:
        nodes: Ordered nodes to render.
        options: Resolved rendering options.
        planner: Wrap planning strategy. Use "chunked" for classic chunk sizing
            and "placement" for placement-core line packing.
    """
    # Canonical dispatch point for all renderer wrap planning.
    if planner == "placement":
        return _build_placement_wrap_plan(nodes=nodes, options=options)
    return _build_chunked_wrap_plan(nodes=nodes, options=options)


def _build_placement_wrap_plan(nodes: list[dict[str, Any]], options: RenderOptions) -> WrapPlan:
    """Build wrap plan using the shared placement core strategy.

    Replaces chunk-based wrapping math with PlacementPlan-derived line breaks
    so line groupings are driven by measured pixel widths rather than a fixed
    chunk size formula.
    """
    if options.layout_wrap != "auto":
        return _inactive_wrap_plan()

    sequence_ids = _collect_sequence_ids(nodes)
    if len(sequence_ids) < 2:
        return _inactive_wrap_plan()

    measures = _sppm_node_measures(nodes=nodes, options=options)
    max_major_px = _sppm_max_major_px(measures=measures, options=options)
    if max_major_px is None:
        return _inactive_wrap_plan()

    constraints = _sppm_placement_constraints(
        orientation=options.orientation, max_major_px=max_major_px
    )
    plan = build_placement_plan(measures, [], constraints)
    if len(plan.lines) <= 1:
        return _inactive_wrap_plan()

    return _wrap_plan_from_placement(plan)


def _inactive_wrap_plan() -> WrapPlan:
    return WrapPlan(
        active=False,
        chunk_size=0,
        chunks=[],
        display_chunks=[],
        boundary_edges=set(),
        node_chunk_index={},
        placement_plan=None,
    )


def _sppm_node_measures(
    *,
    nodes: list[dict[str, Any]],
    options: RenderOptions,
) -> list[NodeMeasure]:
    measures: list[NodeMeasure] = []
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        kind = str(node.get("kind") or node.get("type") or "task").strip().lower()
        width_px = _estimate_sppm_node_width_px(node=node, kind=kind, options=options)
        measures.append(
            NodeMeasure(id=node_id, width_px=width_px, height_px=_DEFAULT_NODE_HEIGHT_PX, kind=kind)
        )
    return measures


def _sppm_max_major_px(
    *,
    measures: list[NodeMeasure],
    options: RenderOptions,
) -> int | None:
    # Convention: when target_columns is supplied, it is the primary intent and
    # therefore takes precedence over layout_max_width_px for deriving the
    # placement budget.
    if options.layout_target_columns and options.layout_target_columns > 0:
        cols = options.layout_target_columns
        if options.orientation == "tb":
            major_dims = [m.height_px for m in measures]
            gap = _VERTICAL_GAP_PX
            default_dim = _DEFAULT_NODE_HEIGHT_PX
        else:
            major_dims = [m.width_px for m in measures]
            gap = _HORIZONTAL_GAP_PX
            default_dim = _DEFAULT_NODE_WIDTH_PX
        if not major_dims:
            return cols * default_dim + max(0, cols - 1) * gap
        dims_sorted = sorted(major_dims)
        p75 = dims_sorted[min(len(dims_sorted) - 1, int(len(dims_sorted) * 0.75))]
        return cols * p75 + max(0, cols - 1) * gap
    if options.layout_max_width_px and options.layout_max_width_px > 0:
        if options.layout_fit == "fit-strict":
            return max(200, options.layout_max_width_px - _STRICT_MARGIN_PX)
        return options.layout_max_width_px
    return None


def _sppm_placement_constraints(
    *,
    orientation: str,
    max_major_px: int,
) -> PlacementConstraints:
    if orientation == "lr":
        return PlacementConstraints(
            orientation="lr",
            max_width_px=max_major_px,
            gap_major=_HORIZONTAL_GAP_PX,
            gap_minor=_VERTICAL_GAP_PX,
            margin=_PREFERRED_MARGIN_PX,
        )
    return PlacementConstraints(
        orientation="tb",
        max_height_px=max_major_px,
        gap_major=_VERTICAL_GAP_PX,
        gap_minor=_HORIZONTAL_GAP_PX,
        margin=_PREFERRED_MARGIN_PX,
    )


def _wrap_plan_from_placement(plan: PlacementPlan) -> WrapPlan:
    chunks = [list(line.node_ids) for line in plan.lines]
    boundary_edges: set[tuple[str, str]] = set()
    for idx in range(len(chunks) - 1):
        boundary_edges.add((chunks[idx][-1], chunks[idx + 1][0]))
    node_chunk_index = {
        node_id: line.line_index
        for line in plan.lines
        for node_id in line.node_ids
    }
    chunk_size = max(len(c) for c in chunks)
    display_chunks = [list(c) for c in chunks]
    return WrapPlan(
        active=True,
        chunk_size=chunk_size,
        chunks=chunks,
        display_chunks=display_chunks,
        boundary_edges=boundary_edges,
        node_chunk_index=node_chunk_index,
        placement_plan=plan,
    )


def _build_chunked_wrap_plan(nodes: list[dict[str, Any]], options: RenderOptions) -> WrapPlan:
    """Build chunk plan for LR rows or TB columns based on current options."""
    if options.layout_wrap != "auto":
        return _inactive_wrap_plan()

    sequence_ids = _collect_sequence_ids(nodes)
    if len(sequence_ids) < 2:
        return _inactive_wrap_plan()

    chunk_size = _resolve_chunk_size(nodes=nodes, options=options)
    if chunk_size <= 0 or len(sequence_ids) <= chunk_size:
        return WrapPlan(
            active=False,
            chunk_size=chunk_size,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
            placement_plan=None,
        )

    chunks = [sequence_ids[i : i + chunk_size] for i in range(0, len(sequence_ids), chunk_size)]
    display_chunks = [_display_chunk_for_layout(chunk=chunk, chunk_idx=idx) for idx, chunk in enumerate(chunks)]
    if len(chunks) <= 1:
        return WrapPlan(
            active=False,
            chunk_size=chunk_size,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
            placement_plan=None,
        )

    boundary_edges: set[tuple[str, str]] = set()
    for idx in range(len(chunks) - 1):
        boundary_edges.add((chunks[idx][-1], chunks[idx + 1][0]))

    node_chunk_index = {
        node_id: chunk_idx
        for chunk_idx, chunk in enumerate(chunks)
        for node_id in chunk
    }

    return WrapPlan(
        active=True,
        chunk_size=chunk_size,
        chunks=chunks,
        display_chunks=display_chunks,
        boundary_edges=boundary_edges,
        node_chunk_index=node_chunk_index,
        placement_plan=None,
    )


def append_wrap_layout_hints(lines: list[str], options: RenderOptions, plan: WrapPlan) -> None:
    """Emit DOT hints that encourage wrapped LR/TB reading layout."""
    if not plan.active:
        return

    orientation = "lr" if options.orientation == "lr" else "tb"
    lines.append(f"  // Autoformat wrapped layout: orientation={orientation}, chunk_size={plan.chunk_size}")

    anchor_ids = [f"__wrap_anchor_{orientation}_{idx}" for idx in range(len(plan.display_chunks))]
    for anchor_id in anchor_ids:
        lines.append(
            f'  "{anchor_id}" [shape=point, width=0.01, label="", style=invis, height=0.01];'
        )

    for chunk_idx, chunk in enumerate(plan.display_chunks):
        if not chunk:
            continue
        cluster_name = f"cluster_wrap_{orientation}_{chunk_idx}"
        lines.append(f"  subgraph {cluster_name} {{")
        lines.append("    color=none;")
        lines.append("    margin=0;")
        lines.append("    rank=same;")
        lines.append(f'    "{anchor_ids[chunk_idx]}";')
        for node_id in chunk:
            lines.append(f'    "{_escape_id(node_id)}";')
        lines.append("  }")

        # Keep a shared left margin for each wrapped chunk.
        first_node = chunk[0]
        lines.append(
            f'  "{anchor_ids[chunk_idx]}" -> "{_escape_id(first_node)}" '
            '[style=invis, weight=200, constraint=false];'
        )

        # Keep chunk sequence deterministic regardless graph branching noise.
        for idx in range(len(chunk) - 1):
            source = chunk[idx]
            target = chunk[idx + 1]
            lines.append(
                f'  "{_escape_id(source)}" -> "{_escape_id(target)}" '
                '[style=invis, weight=100, constraint=false];'
            )

    # Vertically/horizontally align chunk anchors to force left-margin reset.
    for idx in range(len(anchor_ids) - 1):
        lines.append(
            f'  "{anchor_ids[idx]}" -> "{anchor_ids[idx + 1]}" '
            '[style=invis, weight=200, constraint=true];'
        )


def _resolve_chunk_size(*, nodes: list[dict[str, Any]], options: RenderOptions) -> int:
    candidates: list[int] = []

    if options.layout_target_columns and options.layout_target_columns > 0:
        candidates.append(options.layout_target_columns)

    if options.layout_max_width_px and options.layout_max_width_px > 0:
        width_based = _resolve_width_based_chunk_size(nodes=nodes, options=options)
        candidates.append(width_based)

    if not candidates:
        return 0
    return min(candidates)


def _resolve_width_based_chunk_size(*, nodes: list[dict[str, Any]], options: RenderOptions) -> int:
    widths = [_estimate_node_width_px(node=node, options=options) for node in nodes if str(node.get("id") or "")]
    min_chunk_size = _min_chunk_size(options)
    max_width_px = options.layout_max_width_px or 0
    if not widths:
        return max(min_chunk_size, max_width_px // _DEFAULT_NODE_WIDTH_PX)

    available_width = max(200, max_width_px - _layout_margin_px(options))
    representative_width = _representative_node_width_px(widths=widths, options=options)
    effective_per_node = representative_width + _HORIZONTAL_GAP_PX
    if effective_per_node <= 0:
        return min_chunk_size

    return max(min_chunk_size, available_width // effective_per_node)


def _representative_node_width_px(*, widths: list[int], options: RenderOptions) -> int:
    sorted_widths = sorted(widths)
    mean_width = int(round(fmean(sorted_widths)))
    percentile_index = min(len(sorted_widths) - 1, int(len(sorted_widths) * 0.75))
    percentile_width = sorted_widths[percentile_index]
    if options.layout_fit == "fit-strict":
        return max(mean_width, percentile_width, sorted_widths[-1] + 40)
    return max(mean_width, percentile_width)


def _layout_margin_px(options: RenderOptions) -> int:
    if options.layout_fit == "fit-strict":
        return _STRICT_MARGIN_PX
    return _PREFERRED_MARGIN_PX


def _min_chunk_size(options: RenderOptions) -> int:
    if options.layout_fit == "fit-strict":
        return _STRICT_MIN_CHUNK_SIZE
    return _PREFERRED_MIN_CHUNK_SIZE


def _estimate_node_width_px(*, node: dict[str, Any], options: RenderOptions) -> int:
    kind = str(node.get("kind") or node.get("type") or "task").strip().lower()
    if options.diagram == "sppm":
        return _estimate_sppm_node_width_px(node=node, kind=kind, options=options)
    return _estimate_generic_node_width_px(node=node, kind=kind, options=options)


def _estimate_generic_node_width_px(*, node: dict[str, Any], kind: str, options: RenderOptions) -> int:
    name = normalize_space(str(node.get("name") or node.get("id") or ""))
    lane = normalize_space(str(node.get("lane") or ""))
    note = normalize_space(str(node.get("note") or "")) if options.show_notes else ""

    lines = [name]
    if options.detail == "verbose":
        lines.append(str(node.get("id") or ""))
        if options.profile == "analysis" and lane:
            lines.append(f"[{kind}|lane:{lane}]")
    if note:
        lines.append(f"Note: {note}")

    longest = max((len(line) for line in lines if line), default=8)
    base = 92 if kind in {"start", "end"} else 110
    if kind == "decision":
        base += 18
    return max(120, min(320, base + longest * 7))


def _estimate_sppm_node_width_px(*, node: dict[str, Any], kind: str, options: RenderOptions) -> int:
    name = str(node.get("name") or node.get("id") or "")
    if kind in {"start", "end"}:
        return max(120, min(260, 90 + len(normalize_space(name)) * 7))

    metadata: dict[str, Any] = node.get("metadata") or {}
    workers: list[Any] = node.get("workers") or []
    note = str(node.get("note") or "")
    description = normalize_space(str(metadata.get("description") or ""))
    header = _format_sppm_width_field(
        name,
        max_len=options.sppm_max_label_step_name,
        options=options,
    )
    ct_line = _format_time_width_field(
        prefix="CT",
        value=metadata.get("cycle_time"),
        suffix="",
        options=options,
    )
    wt_line = _format_time_width_field(
        prefix="WT",
        value=metadata.get("wait_time"),
        suffix=" wait",
        options=options,
    )
    workers_line = _format_workers_width_field(workers=workers, options=options)
    notes_line = normalize_space(f"Note: {note}") if note and options.show_notes else ""

    info_lines = apply_density_filter(
        density=options.sppm_label_density,
        description=description,
        ct_line=ct_line,
        wt_line=wt_line,
        workers_line=workers_line,
        notes_line=notes_line,
    )
    all_lines = [*header.split("\n"), *(line_part for line in info_lines for line_part in line.split("\n"))]
    longest = max((len(line) for line in all_lines if line), default=12)
    return max(180, min(420, 88 + longest * 7))


def _format_sppm_width_field(raw: str, *, max_len: int | None, options: RenderOptions) -> str:
    return format_text_field(
        raw,
        max_len=max_len,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )


def _format_time_width_field(
    *,
    prefix: str,
    value: Any,
    suffix: str,
    options: RenderOptions,
) -> str:
    if not isinstance(value, dict) or value.get("value") is None:
        return ""
    unit = value.get("unit", "min")
    return _format_sppm_width_field(
        f"{prefix}: {value['value']} {unit}{suffix}",
        max_len=options.sppm_max_label_ctwt,
        options=options,
    )


def _format_workers_width_field(*, workers: list[Any], options: RenderOptions) -> str:
    if not workers:
        return ""
    worker_names = [str(worker) for worker in workers]
    workers_text = ", ".join(worker_names)
    if options.sppm_label_density == "compact":
        workers_text = abbreviate_workers(worker_names)
    return _format_sppm_width_field(
        f"Workers: {workers_text}",
        max_len=options.sppm_max_label_workers,
        options=options,
    )


def _collect_sequence_ids(nodes: list[dict[str, Any]]) -> list[str]:
    sequence: list[str] = []
    for node in nodes:
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        sequence.append(node_id)
    return sequence


def _display_chunk_for_layout(*, chunk: list[str], chunk_idx: int) -> list[str]:
    # Keep chunk order stable to preserve intuitive left-to-right/top-to-bottom flow.
    return list(chunk)


def _escape_id(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
