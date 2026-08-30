"""Deterministic static timing analysis over canonical FLO IR."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import fsum
from typing import Any, Iterable, Literal, cast

from flo.process.ir.metadata import extract_node_metadata
from flo.process.ir.models import IR, Node

from .graph import build_adjacency, enumerate_paths, has_cycle
from .process_metadata import extract_process_metadata


TimingSeverity = Literal["info", "warning"]

_SECONDS_PER_UNIT = {
    "s": 1.0,
    "m": 60.0,
    "min": 60.0,
    "hr": 3600.0,
    "d": 86400.0,
}
_WORK_NODE_TYPES = frozenset({"task", "system_task", "subprocess"})
_PARALLEL_NODE_TYPES = frozenset({"parallel_split", "parallel_join"})
_CHANGEOVER_FIELDS = ("crossover_time", "transfer_time", "changeover_time")
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

    cycle_time_seconds: float = 0.0
    wait_time_seconds: float = 0.0
    changeover_time_seconds: float = 0.0

    @property
    def elapsed_time_seconds(self) -> float:
        """Return the modeled elapsed subtotal represented by these categories."""
        return fsum(
            (
                self.cycle_time_seconds,
                self.wait_time_seconds,
                self.changeover_time_seconds,
            )
        )

    def as_dict(self) -> dict[str, float]:
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

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "changeover_source_field": self.changeover_source_field,
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
    changeover_exposure_policy: str = "one_declared_changeover_per_visited_step"

    @property
    def timing_complete(self) -> bool:
        """Return whether every time-bearing node declares its expected timing."""
        return not self.missing_timing_node_ids

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
        return min(path.totals.elapsed_time_seconds for path in self.paths)

    @property
    def maximum_path_lead_time_seconds(self) -> float | None:
        """Return the maximum lead time when every enumerated path is complete."""
        if not self.paths or not all(path.complete for path in self.paths):
            return None
        return max(path.totals.elapsed_time_seconds for path in self.paths)

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
    node_timings = tuple(
        _analyze_node_timing(node, diagnostics=diagnostics)
        for node in sorted(process.nodes, key=lambda item: item.id)
    )
    timing_by_node = {timing.node_id: timing for timing in node_timings}
    missing_node_ids = tuple(
        sorted(
            node.id
            for node in process.nodes
            if _expected_timing_field(node) is not None
            and not _has_expected_timing(node)
        )
    )
    if missing_node_ids:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-incomplete",
                severity="warning",
                message=(
                    "Modeled lead time is incomplete because expected timing is "
                    f"missing on: {', '.join(missing_node_ids)}."
                ),
            )
        )

    declared_totals = _sum_totals(timing.totals for timing in node_timings)
    paths = _analyze_paths(
        process,
        timing_by_node=timing_by_node,
        missing_node_ids=frozenset(missing_node_ids),
        diagnostics=diagnostics,
    )
    process_metadata = extract_process_metadata(process)
    process_id = _process_identity_text(
        process_metadata.get("process_id"), process.name
    )
    process_name = _process_identity_text(
        process_metadata.get("process_name"), process.name
    )
    return ProcessTimingAnalysis(
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
    diagnostics: list[TimingDiagnostic],
) -> NodeTiming:
    metadata = extract_node_metadata(node)
    cycle_seconds = _duration_seconds(
        metadata.get("cycle_time"),
        node_id=node.id,
        field="cycle_time",
        diagnostics=diagnostics,
    )
    wait_seconds = _duration_seconds(
        metadata.get("wait_time"),
        node_id=node.id,
        field="wait_time",
        diagnostics=diagnostics,
    )
    changeover_field = _select_changeover_field(
        metadata,
        node_id=node.id,
        diagnostics=diagnostics,
    )
    changeover_seconds = _duration_seconds(
        metadata.get(changeover_field) if changeover_field else None,
        node_id=node.id,
        field=changeover_field or "changeover_time",
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
        changeover_source_field=changeover_field,
    )


def _duration_seconds(
    raw: object,
    *,
    node_id: str,
    field: str,
    diagnostics: list[TimingDiagnostic],
) -> float:
    if raw is None:
        return 0.0
    if not isinstance(raw, dict):
        _append_invalid_duration_diagnostic(diagnostics, node_id=node_id, field=field)
        return 0.0
    duration = cast(dict[str, object], raw)
    value = duration.get("value")
    unit = duration.get("unit")
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or float(value) < 0
        or not isinstance(unit, str)
        or unit.strip().lower() not in _SECONDS_PER_UNIT
    ):
        _append_invalid_duration_diagnostic(diagnostics, node_id=node_id, field=field)
        return 0.0
    return float(value) * _SECONDS_PER_UNIT[unit.strip().lower()]


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
            message=f"Ignored invalid timing value at node '{node_id}' metadata.{field}.",
            node_id=node_id,
            field=field,
        )
    )


def _select_changeover_field(
    metadata: dict[str, Any],
    *,
    node_id: str,
    diagnostics: list[TimingDiagnostic],
) -> str | None:
    present = tuple(field for field in _CHANGEOVER_FIELDS if field in metadata)
    if len(present) > 1:
        diagnostics.append(
            TimingDiagnostic(
                code="timing-ambiguous-changeover-fields",
                severity="warning",
                message=(
                    f"Node '{node_id}' declares multiple setup/changeover fields "
                    f"({', '.join(present)}); using '{present[0]}' by compatibility precedence."
                ),
                node_id=node_id,
                field=present[0],
            )
        )
    return present[0] if present else None


def _expected_timing_field(node: Node) -> str | None:
    node_type = node.type.strip().lower()
    if node_type == "queue":
        return "wait_time"
    if node_type in _WORK_NODE_TYPES:
        return "cycle_time"
    return None


def _has_expected_timing(node: Node) -> bool:
    expected_field = _expected_timing_field(node)
    if expected_field is None:
        return True
    return _is_duration_spec(extract_node_metadata(node).get(expected_field))


def _is_duration_spec(raw: object) -> bool:
    if not isinstance(raw, dict):
        return False
    duration = cast(dict[str, object], raw)
    value = duration.get("value")
    unit = duration.get("unit")
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and float(value) >= 0
        and isinstance(unit, str)
        and unit.strip().lower() in _SECONDS_PER_UNIT
    )


def _analyze_paths(
    process: IR,
    *,
    timing_by_node: dict[str, NodeTiming],
    missing_node_ids: frozenset[str],
    diagnostics: list[TimingDiagnostic],
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
) -> TimingPath:
    missing_on_path = tuple(
        node_id for node_id in node_ids if node_id in missing_node_ids
    )
    totals = _sum_totals(
        timing_by_node[node_id].totals
        for node_id in node_ids
        if node_id in timing_by_node
    )
    return TimingPath(
        node_ids=node_ids,
        totals=totals,
        complete=not missing_on_path,
        missing_node_ids=missing_on_path,
    )


def _sum_totals(values: Iterable[TimingTotals]) -> TimingTotals:
    totals = tuple(values)
    return TimingTotals(
        cycle_time_seconds=fsum(item.cycle_time_seconds for item in totals),
        wait_time_seconds=fsum(item.wait_time_seconds for item in totals),
        changeover_time_seconds=fsum(item.changeover_time_seconds for item in totals),
    )


__all__ = [
    "NodeTiming",
    "ProcessTimingAnalysis",
    "TimingDiagnostic",
    "TimingPath",
    "TimingTotals",
    "analyze_process_timing",
]
