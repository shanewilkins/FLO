"""Orientation-aware autoformat wrapping planner shared across DOT renderers."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Any

from .options import RenderOptions
from ._sppm_text import apply_density_filter, abbreviate_workers, format_text_field, normalize_space

_DEFAULT_NODE_WIDTH_PX = 220
_PREFERRED_MIN_CHUNK_SIZE = 3
_STRICT_MIN_CHUNK_SIZE = 2
_HORIZONTAL_GAP_PX = 48
_PREFERRED_MARGIN_PX = 48
_STRICT_MARGIN_PX = 180


@dataclass(frozen=True)
class AutoformatWrapPlan:
    """Deterministic wrap plan for sequence-oriented layout."""

    active: bool
    chunk_size: int
    chunks: list[list[str]]
    display_chunks: list[list[str]]
    boundary_edges: set[tuple[str, str]]
    node_chunk_index: dict[str, int]


def build_autoformat_wrap_plan(nodes: list[dict[str, Any]], options: RenderOptions) -> AutoformatWrapPlan:
    """Build chunk plan for LR rows or TB columns based on current options."""
    if options.layout_wrap != "auto":
        return AutoformatWrapPlan(
            active=False,
            chunk_size=0,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
        )

    sequence_ids = _collect_sequence_ids(nodes)
    if len(sequence_ids) < 2:
        return AutoformatWrapPlan(
            active=False,
            chunk_size=0,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
        )

    chunk_size = _resolve_chunk_size(nodes=nodes, options=options)
    if chunk_size <= 0 or len(sequence_ids) <= chunk_size:
        return AutoformatWrapPlan(
            active=False,
            chunk_size=chunk_size,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
        )

    chunks = [sequence_ids[i : i + chunk_size] for i in range(0, len(sequence_ids), chunk_size)]
    display_chunks = [_display_chunk_for_layout(chunk=chunk, chunk_idx=idx) for idx, chunk in enumerate(chunks)]
    if len(chunks) <= 1:
        return AutoformatWrapPlan(
            active=False,
            chunk_size=chunk_size,
            chunks=[],
            display_chunks=[],
            boundary_edges=set(),
            node_chunk_index={},
        )

    boundary_edges: set[tuple[str, str]] = set()
    for idx in range(len(chunks) - 1):
        boundary_edges.add((chunks[idx][-1], chunks[idx + 1][0]))

    node_chunk_index = {
        node_id: chunk_idx
        for chunk_idx, chunk in enumerate(chunks)
        for node_id in chunk
    }

    return AutoformatWrapPlan(
        active=True,
        chunk_size=chunk_size,
        chunks=chunks,
        display_chunks=display_chunks,
        boundary_edges=boundary_edges,
        node_chunk_index=node_chunk_index,
    )


def append_wrap_layout_hints(lines: list[str], options: RenderOptions, plan: AutoformatWrapPlan) -> None:
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
