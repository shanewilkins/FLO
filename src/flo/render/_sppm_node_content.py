"""Backend-neutral SPPM node content and measurement helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.schema.subprocess_refs import resolve_subprocess_detail_map_reference

from ._sppm_metadata_schema import (
    get_metadata_crossover_time,
    get_metadata_cycle_time,
    get_metadata_description,
    get_metadata_wait_time_minutes,
)
from ._sppm_text import (
    abbreviate_workers,
    apply_density_filter,
    format_text_field,
    normalize_space,
)
from .options import RenderOptions

_TASK_MIN_WIDTH_PX = 160
_TASK_MAX_WIDTH_PX = 320
_TASK_BASE_HEIGHT_PX = 54
_TASK_LINE_HEIGHT_PX = 16
_TASK_HEADER_WRAP = 24
_TASK_DESC_WRAP = 42
_TASK_WORKERS_WRAP = 36
_DECISION_HEADER_WRAP = 18
_DECISION_MIN_WIDTH_PX = 158
_DECISION_MIN_HEIGHT_PX = 90
_QUEUE_HEADER_WRAP = 18
_QUEUE_MIN_WIDTH_PX = 150
_QUEUE_MIN_HEIGHT_PX = 150
_SUBPROCESS_MIN_WIDTH_PX = 190
_SUBPROCESS_MIN_HEIGHT_PX = 92
_START_END_WIDTH_PX = 132
_START_END_HEIGHT_PX = 52


@dataclass(frozen=True)
class SppmNodeContent:
    """Renderer-neutral display content for one SPPM node."""

    title: str
    info_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class SppmNodeMeasure:
    """Renderer-neutral node size estimate for ELK layout."""

    width_px: int
    height_px: int


def build_sppm_node_content(
    *,
    node_id: str,
    kind: str,
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    note: str,
    options: RenderOptions,
) -> SppmNodeContent:
    """Build the title and supporting lines for an SPPM node."""
    normalized_kind = str(kind or "task").lower()
    if normalized_kind == "queue":
        return _queue_content(name=name, metadata=metadata, options=options)
    if normalized_kind == "subprocess":
        return _subprocess_content(
            node_id=node_id,
            name=name,
            metadata=metadata,
            options=options,
        )
    if normalized_kind == "decision":
        return SppmNodeContent(
            title=_wrap_decision_title(name=name, options=options),
            info_lines=(),
        )

    title = _wrap_title(name=name, options=options)
    info_lines = _task_info_lines(
        metadata=metadata,
        workers=workers,
        note=note,
        options=options,
    )
    return SppmNodeContent(title=title, info_lines=info_lines)


def measure_sppm_node(
    *,
    node_id: str,
    kind: str,
    name: str,
    metadata: dict[str, Any],
    workers: list[Any],
    note: str,
    options: RenderOptions,
) -> SppmNodeMeasure:
    """Estimate ELK node bounds from SPPM display content."""
    normalized_kind = str(kind or "task").lower()
    content = build_sppm_node_content(
        node_id=node_id,
        kind=normalized_kind,
        name=name,
        metadata=metadata,
        workers=workers,
        note=note,
        options=options,
    )

    if normalized_kind == "decision":
        width = max(_DECISION_MIN_WIDTH_PX, 112 + (_widest_line_length(content) * 7))
        height = max(
            _DECISION_MIN_HEIGHT_PX,
            62 + (_line_count(content.title) * 26),
        )
        return SppmNodeMeasure(
            width_px=min(width, 280),
            height_px=min(height, 164),
        )
    if normalized_kind == "queue":
        line_count = _line_count(content.title) + _multi_line_count(content.info_lines)
        height = max(_QUEUE_MIN_HEIGHT_PX, 82 + (line_count * 14))
        width = max(_QUEUE_MIN_WIDTH_PX, 124 + (_widest_line_length(content) * 5))
        return SppmNodeMeasure(width_px=min(width, 220), height_px=min(height, 196))
    if normalized_kind == "subprocess":
        width = max(_SUBPROCESS_MIN_WIDTH_PX, 140 + (_widest_line_length(content) * 4))
        height = max(
            _SUBPROCESS_MIN_HEIGHT_PX,
            64
            + (
                (_line_count(content.title) + _multi_line_count(content.info_lines))
                * 14
            ),
        )
        return SppmNodeMeasure(width_px=min(width, 300), height_px=min(height, 148))
    if normalized_kind in {"start", "end"}:
        return SppmNodeMeasure(
            width_px=_START_END_WIDTH_PX, height_px=_START_END_HEIGHT_PX
        )

    width = max(_TASK_MIN_WIDTH_PX, 120 + (_widest_line_length(content) * 5))
    height = max(
        _TASK_BASE_HEIGHT_PX,
        _TASK_BASE_HEIGHT_PX
        + (
            (_line_count(content.title) + _multi_line_count(content.info_lines))
            * _TASK_LINE_HEIGHT_PX
        ),
    )
    return SppmNodeMeasure(
        width_px=min(width, _TASK_MAX_WIDTH_PX),
        height_px=min(height, 220),
    )


def _queue_content(
    *, name: str, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeContent:
    if options.sppm_max_label_step_name is None:
        title = _soft_wrap(normalize_space(name), width=_QUEUE_HEADER_WRAP)
    else:
        title = format_text_field(
            normalize_space(name),
            max_len=min(options.sppm_max_label_step_name, _QUEUE_HEADER_WRAP),
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )
    wait_minutes = get_metadata_wait_time_minutes(metadata)
    info_lines = (f"WT: {wait_minutes:g} min",) if wait_minutes else ()
    return SppmNodeContent(title=title or "Q", info_lines=info_lines)


def _subprocess_content(
    *, node_id: str, name: str, metadata: dict[str, Any], options: RenderOptions
) -> SppmNodeContent:
    title = _wrap_title(name=name, options=options)
    detail_map_ref = resolve_subprocess_detail_map_reference(
        node_id=node_id,
        metadata=metadata,
    )
    return SppmNodeContent(
        title=title,
        info_lines=("Subprocess", f"Detail map: {detail_map_ref}"),
    )


def _task_info_lines(
    *,
    metadata: dict[str, Any],
    workers: list[Any],
    note: str,
    options: RenderOptions,
) -> tuple[str, ...]:
    description = _soft_wrap(
        normalize_space(get_metadata_description(metadata)), width=_TASK_DESC_WRAP
    )
    ct_line = _format_time_line(get_metadata_cycle_time(metadata), "CT", "", options)
    wt_line = _format_time_line(
        get_metadata_wait_time_minutes(metadata),
        "WT",
        " wait",
        options,
        require_positive=True,
    )
    co_line = _format_time_line(
        get_metadata_crossover_time(metadata),
        "CO",
        " crossover",
        options,
        require_positive=True,
    )
    workers_line = _format_workers_line(workers, options)
    notes_line = (
        f"Note: {normalize_space(note)}"
        if note and getattr(options, "show_notes", False)
        else ""
    )
    return tuple(
        apply_density_filter(
            density=options.sppm_label_density,
            description=description,
            ct_line=ct_line,
            wt_line=wt_line,
            co_line=co_line,
            workers_line=workers_line,
            notes_line=notes_line,
        )
    )


def _wrap_title(*, name: str, options: RenderOptions) -> str:
    if options.sppm_max_label_step_name is None:
        return _soft_wrap(normalize_space(name), width=_TASK_HEADER_WRAP)
    return format_text_field(
        name,
        max_len=options.sppm_max_label_step_name,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )


def _wrap_decision_title(*, name: str, options: RenderOptions) -> str:
    if options.sppm_max_label_step_name is None:
        return _soft_wrap(normalize_space(name), width=_DECISION_HEADER_WRAP)
    return format_text_field(
        name,
        max_len=min(options.sppm_max_label_step_name, _DECISION_HEADER_WRAP),
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )


def _format_workers_line(workers: list[Any], options: RenderOptions) -> str:
    if not workers:
        return ""
    workers_text = (
        abbreviate_workers([str(worker) for worker in workers])
        if options.sppm_label_density == "compact"
        else ", ".join(str(worker) for worker in workers)
    )
    if options.sppm_max_label_workers is None:
        return _soft_wrap(f"Workers: {workers_text}", width=_TASK_WORKERS_WRAP)
    return format_text_field(
        f"Workers: {workers_text}",
        max_len=options.sppm_max_label_workers,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )


def _format_time_line(
    value: Any,
    prefix: str,
    suffix: str,
    options: RenderOptions,
    *,
    require_positive: bool = False,
) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if require_positive and value <= 0:
            return ""
        value_str = (
            str(int(value))
            if isinstance(value, float) and value.is_integer()
            else str(value)
        )
        return format_text_field(
            f"{prefix}: {value_str} min{suffix}",
            max_len=options.sppm_max_label_ctwt,
            wrap_strategy=options.sppm_wrap_strategy,
            truncation_policy=options.sppm_truncation_policy,
            html_break="\n",
        )
    if require_positive and value.numeric_value <= 0:
        return ""
    return format_text_field(
        f"{prefix}: {value.value} {value.unit or 'min'}{suffix}",
        max_len=options.sppm_max_label_ctwt,
        wrap_strategy=options.sppm_wrap_strategy,
        truncation_policy=options.sppm_truncation_policy,
        html_break="\n",
    )


def _soft_wrap(text: str, *, width: int) -> str:
    return format_text_field(
        text,
        max_len=width,
        wrap_strategy="soft",
        truncation_policy="none",
        html_break="\n",
    )


def _widest_line_length(content: SppmNodeContent) -> int:
    lines = [*content.title.split("\n")]
    for line in content.info_lines:
        lines.extend(line.split("\n"))
    return max((len(line) for line in lines if line), default=0)


def _line_count(text: str) -> int:
    return text.count("\n") + 1 if text else 0


def _multi_line_count(lines: tuple[str, ...]) -> int:
    return sum(_line_count(line) for line in lines)
