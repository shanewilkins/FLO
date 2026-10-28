"""Deterministic static timing analysis over canonical FLO IR."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from math import fsum, isfinite
from typing import Any, Literal

from flo.process.durations import duration_seconds
from flo.process.ir.models import IR, Node
from flo.process.ir.wait_measurements import (
    WORK_NODE_TYPES as _WORK_NODE_TYPES,
)
from flo.process.ir.wait_measurements import queue_wait_projections
from flo.process.measurements import measurement_reference, selected_result

from .graph import build_adjacency, enumerate_paths, has_cycle
from .process_metadata import extract_process_metadata

TimingSeverity = Literal["info", "warning"]

_MISSING = object()
_PARALLEL_NODE_TYPES = frozenset({"parallel_split", "parallel_join"})
_MAX_PATHS = 256


@dataclass(frozen=True)
class TimingDiagnostic:
    """A deterministic limitation or data-quality finding from timing analysis."""

    code: str
    severity: TimingSeverity
    message: str
    node_id: str | None = None
    field: str | None = None


@dataclass(frozen=True)
class TimingTotals:
    """Normalized timing category totals in seconds."""

    cycle_time_seconds: float | None = None
    wait_time_seconds: float | None = None
    changeover_time_seconds: float | None = None
    _overflowed: bool = field(default=False, repr=False)
    _incomplete: bool = field(default=False, repr=False)

    @property
    def elapsed_time_seconds(self) -> float | None:
        """Return the modeled elapsed subtotal represented by these categories."""
        values = tuple(
            value
            for value in (
                self.cycle_time_seconds,
                self.wait_time_seconds,
                self.changeover_time_seconds,
            )
            if value is not None
        )
        return None if self._overflowed or self._incomplete else _finite_sum(values)

    def as_dict(self) -> dict[str, float | None]:
        """Return a stable JSON-compatible representation."""
        return {
            "cycle_time_seconds": self.cycle_time_seconds,
            "wait_time_seconds": self.wait_time_seconds,
            "changeover_time_seconds": self.changeover_time_seconds,
            "elapsed_time_seconds": self.elapsed_time_seconds,
        }


@dataclass(frozen=True)
class NodeTiming:
    """Normalized timing contribution declared by one canonical node."""

    node_id: str
    node_type: str
    totals: TimingTotals
    changeover_source_field: str | None = None
    declared_wait_time_seconds: float | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "changeover_source_field": self.changeover_source_field,
            "declared_wait_time_seconds": self.declared_wait_time_seconds,
            "totals": self.totals.as_dict(),
        }


@dataclass(frozen=True)
class TimingPath:
    """One deterministic acyclic start-to-end path and its declared timing."""

    node_ids: tuple[str, ...]
    totals: TimingTotals
    complete: bool
    missing_node_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "node_ids": list(self.node_ids),
            "complete": self.complete,
            "missing_node_ids": list(self.missing_node_ids),
            "totals": self.totals.as_dict(),
        }


@dataclass(frozen=True)
class ProcessTimingAnalysis:
    """Typed timing-analysis result for one canonical process."""

    analysis_version: str
    process_id: str
    process_name: str
    process_version: int | str | None
    node_timings: tuple[NodeTiming, ...]
    declared_totals: TimingTotals
    paths: tuple[TimingPath, ...]
    missing_timing_node_ids: tuple[str, ...]
    diagnostics: tuple[TimingDiagnostic, ...]
    supplied_lead_time: dict[str, Any] | None = None
    changeover_exposure_policy: str = "one_declared_changeover_per_visited_step"

    @property
    def timing_complete(self) -> bool:
        """Return whether every time-bearing node declares its expected timing."""
        return not self.missing_timing_node_ids and all(
            path.complete for path in self.paths
        )

    @property
    def modeled_lead_time_seconds(self) -> float | None:
        """Return one complete path lead time, or None when no single value exists."""
        if len(self.paths) != 1 or not self.paths[0].complete:
            return None
        return self.paths[0].totals.elapsed_time_seconds

    @property
    def minimum_path_lead_time_seconds(self) -> float | None:
        """Return the minimum lead time when every enumerated path is complete."""
        if not self.paths or not all(path.complete for path in self.paths):
            return None
        elapsed_times = tuple(path.totals.elapsed_time_seconds for path in self.paths)
        if any(value is None for value in elapsed_times):
            return None
        return min(value for value in elapsed_times if value is not None)

    @property
    def maximum_path_lead_time_seconds(self) -> float | None:
        """Return the maximum lead time when every enumerated path is complete."""
        if not self.paths or not all(path.complete for path in self.paths):
            return None
        elapsed_times = tuple(path.totals.elapsed_time_seconds for path in self.paths)
        if any(value is None for value in elapsed_times):
            return None
        return max(value for value in elapsed_times if value is not None)

    def as_dict(self) -> dict[str, Any]:
        """Return the initial stable, JSON-compatible timing analysis shape."""
        return {
            "analysis_version": self.analysis_version,
            "process": {
                "id": self.process_id,
                "name": self.process_name,
                "version": self.process_version,
            },
            "changeover_exposure_policy": self.changeover_exposure_policy,
            "timing_complete": self.timing_complete,
            "supplied_lead_time": deepcopy(self.supplied_lead_time),
            "modeled_lead_time_seconds": self.modeled_lead_time_seconds,
            "minimum_path_lead_time_seconds": self.minimum_path_lead_time_seconds,
            "maximum_path_lead_time_seconds": self.maximum_path_lead_time_seconds,
            "missing_timing_node_ids": list(self.missing_timing_node_ids),
            "declared_totals": self.declared_totals.as_dict(),
            "node_timings": [timing.as_dict() for timing in self.node_timings],
            "paths": [path.as_dict() for path in self.paths],
            "diagnostics": [asdict(diagnostic) for diagnostic in self.diagnostics],
        }


def analyze_process_timing(process: IR) -> ProcessTimingAnalysis:
    """Analyze declared timing without mutating or guessing beyond canonical IR."""
    if not isinstance(process, IR):
        raise TypeError("analyze_process_timing requires canonical IR")

    diagnostics: list[TimingDiagnostic] = []
    projections = queue_wait_projections(process)
    nodes_by_id = {node.id: node for node in process.nodes}
    raw_timings = tuple(
        _analyze_node_timing(
            node,
            nodes_by_id=nodes_by_id,
            diagnostics=diagnostics,
        )
        for node in sorted(process.nodes, key=lambda item: item.id)
    )
    node_timings = _inventory_timings(raw_timings, projections)
    timing_by_node = {timing.node_id: timing for timing in node_timings}
    invalid_node_ids = {
        item.node_id for item in diagnostics if item.code == "timing-invalid-duration"
    }
    missing_node_ids = tuple(
        sorted(
            node.id
            for node in process.nodes
            if node.id in invalid_node_ids
            or (
                _expected_timing_field(node) is not None
                and not _has_expected_timing(node)
            )
        )
    )
    if missing_node_ids:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-incomplete",
                severity="warning",
                message=(
                    "Modeled lead time is incomplete because expected timing is "
                    f"missing or invalid on: {', '.join(missing_node_ids)}."
                ),
            )
        )

    declared_totals = _sum_totals(
        (timing.totals for timing in node_timings), diagnostics=diagnostics
    )
    paths = _analyze_paths(
        process,
        timing_by_node=timing_by_node,
        missing_node_ids=frozenset(missing_node_ids),
        diagnostics=diagnostics,
        projections=projections,
    )
    missing_node_ids = tuple(
        sorted(
            set(missing_node_ids)
            | {node_id for path in paths for node_id in path.missing_node_ids}
        )
    )
    process_metadata = extract_process_metadata(process)
    process_id = _process_identity_text(
        process_metadata.get("process_id"), process.name
    )
    process_name = _process_identity_text(
        process_metadata.get("process_name"), process.name
    )
    return ProcessTimingAnalysis(
        supplied_lead_time=deepcopy(process.lead_time),
        analysis_version="0.1",
        process_id=process_id,
        process_name=process_name,
        process_version=process.process_version,
        node_timings=node_timings,
        declared_totals=declared_totals,
        paths=paths,
        missing_timing_node_ids=missing_node_ids,
        diagnostics=tuple(diagnostics),
    )


def _process_identity_text(raw: object, fallback: str) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return fallback


def _analyze_node_timing(
    node: Node,
    *,
    nodes_by_id: dict[str, Node],
    diagnostics: list[TimingDiagnostic],
) -> NodeTiming:
    cycle_seconds = _duration_seconds(
        selected_result(node.cycle_time) if node.cycle_time is not None else _MISSING,
        node_id=node.id,
        field="cycle_time",
        diagnostics=diagnostics,
    )
    wait_measurement = _resolve_wait_measurement(node, nodes_by_id)
    wait_seconds = _duration_seconds(
        selected_result(wait_measurement) if wait_measurement is not None else _MISSING,
        node_id=node.id,
        field="wait_time",
        diagnostics=diagnostics,
    )
    changeover_seconds = _duration_seconds(
        selected_result(node.changeover_time)
        if node.changeover_time is not None
        else _MISSING,
        node_id=node.id,
        field="changeover_time",
        diagnostics=diagnostics,
    )
    return NodeTiming(
        node_id=node.id,
        node_type=node.type.strip().lower(),
        totals=TimingTotals(
            cycle_time_seconds=cycle_seconds,
            wait_time_seconds=wait_seconds,
            changeover_time_seconds=changeover_seconds,
        ),
        changeover_source_field=(
            "changeover_time" if node.changeover_time is not None else None
        ),
        declared_wait_time_seconds=wait_seconds,
    )


def _resolve_wait_measurement(
    node: Node, nodes_by_id: dict[str, Node]
) -> dict[str, Any] | None:
    reference = measurement_reference(node.wait_time)
    if reference is None:
        return node.wait_time
    target = nodes_by_id.get(reference[0])
    return target.wait_time if target is not None else None


def _inventory_timings(
    timings: tuple[NodeTiming, ...],
    projections: dict[str, frozenset[str]],
) -> tuple[NodeTiming, ...]:
    inventory: list[NodeTiming] = []
    for timing in timings:
        if timing.node_id in projections:
            timing = replace(
                timing, totals=replace(timing.totals, wait_time_seconds=None)
            )
        inventory.append(timing)
    return tuple(inventory)


def _duration_seconds(
    raw: object,
    *,
    node_id: str,
    field: str,
    diagnostics: list[TimingDiagnostic],
) -> float | None:
    if raw is _MISSING:
        return None
    seconds = duration_seconds(raw)
    if seconds is None:
        _append_invalid_duration_diagnostic(diagnostics, node_id=node_id, field=field)
    return seconds


def _append_invalid_duration_diagnostic(
    diagnostics: list[TimingDiagnostic],
    *,
    node_id: str,
    field: str,
) -> None:
    diagnostics.append(
        TimingDiagnostic(
            code="timing-invalid-duration",
            severity="warning",
            message=f"Ignored invalid timing value at node '{node_id}' field '{field}'.",
            node_id=node_id,
            field=field,
        )
    )


def _expected_timing_field(node: Node) -> str | None:
    node_type = node.type.strip().lower()
    if node_type in {"queue", "wait"}:
        return "wait_time"
    if node_type in _WORK_NODE_TYPES:
        return "cycle_time"
    return None


def _has_expected_timing(node: Node) -> bool:
    expected_field = _expected_timing_field(node)
    if expected_field is None:
        return True
    measurement = getattr(node, expected_field)
    if measurement_reference(measurement) is not None:
        return True
    return _is_duration_spec(selected_result(measurement))


def _is_duration_spec(raw: object) -> bool:
    return duration_seconds(raw) is not None


def _analyze_paths(
    process: IR,
    *,
    timing_by_node: dict[str, NodeTiming],
    missing_node_ids: frozenset[str],
    diagnostics: list[TimingDiagnostic],
    projections: dict[str, frozenset[str]],
) -> tuple[TimingPath, ...]:
    if any(node.type.strip().lower() in _PARALLEL_NODE_TYPES for node in process.nodes):
        diagnostics.append(
            TimingDiagnostic(
                code="timing-parallel-flow-unsupported",
                severity="warning",
                message=(
                    "Path lead time is not modeled for parallel split/join flow in "
                    "the initial static timing analysis."
                ),
            )
        )
        return ()

    adjacency = build_adjacency(process)
    if has_cycle(adjacency):
        diagnostics.append(
            TimingDiagnostic(
                code="timing-cycle-unsupported",
                severity="warning",
                message=(
                    "Path lead time is not modeled for cyclic or rework flow without "
                    "an explicit iteration policy."
                ),
            )
        )
        return ()

    start_ids = sorted(
        node.id for node in process.nodes if node.type.strip().lower() == "start"
    )
    end_ids = {node.id for node in process.nodes if node.type.strip().lower() == "end"}
    if len(start_ids) != 1 or not end_ids:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-invalid-boundary",
                severity="warning",
                message="Path timing requires exactly one start and at least one end node.",
            )
        )
        return ()

    raw_paths, truncated = enumerate_paths(
        start_id=start_ids[0],
        end_ids=end_ids,
        adjacency=adjacency,
        limit=_MAX_PATHS,
    )
    if truncated:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-path-limit",
                severity="warning",
                message=f"Path timing stopped after the deterministic limit of {_MAX_PATHS} paths.",
            )
        )
        return ()
    if not raw_paths:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-no-complete-path",
                severity="warning",
                message="No complete start-to-end path was available for timing analysis.",
            )
        )
        return ()

    paths = tuple(
        _build_timing_path(
            node_ids=path,
            timing_by_node=timing_by_node,
            missing_node_ids=missing_node_ids,
            diagnostics=diagnostics,
            projections=projections,
        )
        for path in raw_paths
    )
    if len(paths) > 1:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-multiple-paths",
                severity="info",
                message=(
                    f"Process has {len(paths)} acyclic start-to-end paths; report a "
                    "range instead of one modeled lead time."
                ),
            )
        )
    return paths


def _build_timing_path(
    *,
    node_ids: tuple[str, ...],
    timing_by_node: dict[str, NodeTiming],
    missing_node_ids: frozenset[str],
    diagnostics: list[TimingDiagnostic],
    projections: dict[str, frozenset[str]],
) -> TimingPath:
    uncovered = {
        node_id
        for node_id in node_ids
        if node_id in projections and not projections[node_id].issubset(node_ids)
    }
    for node_id in sorted(uncovered):
        if not any(
            item.code == "timing-projection-incomplete" and item.node_id == node_id
            for item in diagnostics
        ):
            diagnostics.append(
                TimingDiagnostic(
                    code="timing-projection-incomplete",
                    severity="warning",
                    message=f"Some paths through queue '{node_id}' lack its full referenced waiting evidence; affected path elapsed totals are unavailable.",
                    node_id=node_id,
                    field="wait_time",
                )
            )
    missing_on_path = tuple(
        node_id
        for node_id in node_ids
        if node_id in missing_node_ids or node_id in uncovered
    )
    totals = _sum_totals(
        (
            _path_node_totals(
                timing_by_node[node_id],
                projections=projections,
                uncovered=uncovered,
            )
            for node_id in node_ids
            if node_id in timing_by_node
        ),
        diagnostics=diagnostics,
    )
    return TimingPath(
        node_ids=node_ids,
        totals=totals,
        complete=not missing_on_path and not totals._overflowed,
        missing_node_ids=missing_on_path,
    )


def _path_node_totals(
    timing: NodeTiming,
    *,
    projections: dict[str, frozenset[str]],
    uncovered: set[str],
) -> TimingTotals:
    if timing.node_id in projections:
        return replace(
            timing.totals,
            wait_time_seconds=None,
            _incomplete=timing.node_id in uncovered,
        )
    return timing.totals


def _sum_totals(
    values: Iterable[TimingTotals],
    *,
    diagnostics: list[TimingDiagnostic],
) -> TimingTotals:
    totals = tuple(values)
    categories = tuple(
        tuple(value for item in totals if (value := getattr(item, name)) is not None)
        for name in (
            "cycle_time_seconds",
            "wait_time_seconds",
            "changeover_time_seconds",
        )
    )
    sums = tuple(_finite_sum(category) for category in categories)
    overflowed = any(item._overflowed for item in totals) or any(
        category and total is None
        for category, total in zip(categories, sums, strict=True)
    )
    overflowed = overflowed or (
        any(value is not None for value in sums)
        and _finite_sum(value for value in sums if value is not None) is None
    )
    if overflowed and not any(
        item.code == "timing-total-overflow" for item in diagnostics
    ):
        diagnostics.append(
            TimingDiagnostic(
                code="timing-total-overflow",
                severity="warning",
                message="Timing totals exceed the finite numeric range; affected elapsed totals are unavailable.",
            )
        )
    return TimingTotals(
        *sums,
        _overflowed=overflowed,
        _incomplete=any(item._incomplete for item in totals),
    )


def _finite_sum(values: Iterable[float]) -> float | None:
    declared = tuple(values)
    if not declared:
        return None
    try:
        total = fsum(declared)
    except OverflowError:
        return None
    return total if isfinite(total) else None


__all__ = [
    "NodeTiming",
    "ProcessTimingAnalysis",
    "TimingDiagnostic",
    "TimingPath",
    "TimingTotals",
    "analyze_process_timing",
]
