"""Deterministic structural analysis over validated canonical FLO IR."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any, Literal

from flo.process.ir.metadata import extract_node_metadata
from flo.process.ir.models import IR, Edge, Node

from .graph import build_adjacency, enumerate_paths, has_cycle
from .process_metadata import extract_process_metadata

StructuralSeverity = Literal["info", "warning"]
HandoffClassification = Literal["explicit", "candidate"]
ReworkClassification = Literal["explicit", "inferred"]

_MAX_PATHS = 256
_PARALLEL_NODE_TYPES = frozenset({"parallel_split", "parallel_join"})
_CLASSIFIABLE_NODE_TYPES = frozenset(
    {"task", "system_task", "subprocess", "queue", "wait"}
)


@dataclass(frozen=True)
class StructuralDiagnostic:
    """A deterministic structural limitation or model-quality finding."""

    code: str
    severity: StructuralSeverity
    message: str
    node_id: str | None = None
    source_id: str | None = None
    target_id: str | None = None


@dataclass(frozen=True)
class HandoffFinding:
    """An explicit handoff or a separately identified lane-change candidate."""

    source_id: str
    target_id: str
    classification: HandoffClassification
    edge_id: str | None = None
    handoff_type: str | None = None
    source_lane: str | None = None
    target_lane: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "classification": self.classification,
            "edge_id": self.edge_id,
            "handoff_type": self.handoff_type,
            "source_lane": self.source_lane,
            "target_lane": self.target_lane,
        }


@dataclass(frozen=True)
class ReworkFinding:
    """An explicit rework edge or deterministic back-edge inference."""

    source_id: str
    target_id: str
    classification: ReworkClassification
    edge_id: str | None = None
    rate: float | None = None
    reason: str | None = None
    count: int | float | str | None = None
    frequency: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "classification": self.classification,
            "edge_id": self.edge_id,
            "rate": self.rate,
            "reason": self.reason,
            "count": self.count,
            "frequency": self.frequency,
        }


@dataclass(frozen=True)
class StructuralPath:
    """One deterministic non-rework start-to-end path."""

    node_ids: tuple[str, ...]

    @property
    def node_count(self) -> int:
        """Return the number of nodes on the path."""
        return len(self.node_ids)

    @property
    def edge_count(self) -> int:
        """Return the graph-theoretic path length in edges."""
        return max(0, len(self.node_ids) - 1)

    @property
    def step_count(self) -> int:
        """Return path nodes excluding start and end boundary nodes."""
        return max(0, len(self.node_ids) - 2)

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "node_ids": list(self.node_ids),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "step_count": self.step_count,
        }


@dataclass(frozen=True)
class StepClassification:
    """The canonical kind and optional Lean value class of one node."""

    node_id: str
    node_type: str
    value_class: str | None

    def as_dict(self) -> dict[str, str | None]:
        """Return a stable JSON-compatible representation."""
        return asdict(self)


@dataclass(frozen=True)
class ProcessStructuralAnalysis:
    """Versioned static structural-analysis result for one process."""

    analysis_version: str
    process_id: str
    process_name: str
    process_version: int | str | None
    handoffs: tuple[HandoffFinding, ...]
    handoff_candidates: tuple[HandoffFinding, ...]
    rework_edges: tuple[ReworkFinding, ...]
    paths: tuple[StructuralPath, ...]
    step_classifications: tuple[StepClassification, ...]
    unclassified_node_ids: tuple[str, ...]
    diagnostics: tuple[StructuralDiagnostic, ...]

    @property
    def minimum_path_edge_count(self) -> int | None:
        """Return the shortest complete non-rework path length."""
        return min((path.edge_count for path in self.paths), default=None)

    @property
    def maximum_path_edge_count(self) -> int | None:
        """Return the longest complete non-rework path length."""
        return max((path.edge_count for path in self.paths), default=None)

    @property
    def node_type_counts(self) -> dict[str, int]:
        """Return deterministic node-kind counts."""
        return _classification_counts(
            classification.node_type for classification in self.step_classifications
        )

    @property
    def value_class_counts(self) -> dict[str, int]:
        """Return deterministic counts for declared Lean value classes."""
        return _classification_counts(
            classification.value_class
            for classification in self.step_classifications
            if classification.value_class is not None
        )

    def as_dict(self) -> dict[str, Any]:
        """Return the stable JSON-compatible structural-analysis shape."""
        return {
            "analysis_version": self.analysis_version,
            "process": {
                "id": self.process_id,
                "name": self.process_name,
                "version": self.process_version,
            },
            "handoffs": [finding.as_dict() for finding in self.handoffs],
            "handoff_candidates": [
                finding.as_dict() for finding in self.handoff_candidates
            ],
            "rework_edges": [finding.as_dict() for finding in self.rework_edges],
            "path_summary": {
                "path_count": len(self.paths),
                "minimum_edge_count": self.minimum_path_edge_count,
                "maximum_edge_count": self.maximum_path_edge_count,
            },
            "paths": [path.as_dict() for path in self.paths],
            "step_classification": {
                "node_type_counts": self.node_type_counts,
                "value_class_counts": self.value_class_counts,
                "unclassified_node_ids": list(self.unclassified_node_ids),
                "nodes": [
                    classification.as_dict()
                    for classification in self.step_classifications
                ],
            },
            "diagnostics": [asdict(diagnostic) for diagnostic in self.diagnostics],
        }


def analyze_process_structure(process: IR) -> ProcessStructuralAnalysis:
    """Analyze canonical structure without telemetry, mutation, or simulation."""
    if not isinstance(process, IR):
        raise TypeError("analyze_process_structure requires canonical IR")

    nodes_by_id = {node.id: node for node in process.nodes}
    node_order = {node.id: index for index, node in enumerate(process.nodes)}
    diagnostics: list[StructuralDiagnostic] = []
    handoffs, candidates = _analyze_handoffs(
        process.edges,
        nodes_by_id=nodes_by_id,
        diagnostics=diagnostics,
    )
    rework_edges = _analyze_rework(
        process.edges,
        node_order=node_order,
        diagnostics=diagnostics,
    )
    primary_edges = tuple(
        edge
        for edge in process.edges
        if _rework_classification(edge, node_order=node_order) is None
    )
    paths = _analyze_paths(
        process,
        primary_edges=primary_edges,
        diagnostics=diagnostics,
    )
    classifications, unclassified = _analyze_step_classification(process.nodes)
    if unclassified:
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-unclassified-steps",
                severity="warning",
                message=(
                    f"Lean value_class is not declared for: {', '.join(unclassified)}."
                ),
            )
        )

    process_metadata = extract_process_metadata(process)
    process_id = _identity_text(process_metadata.get("process_id"), process.name)
    process_name = _identity_text(process_metadata.get("process_name"), process.name)
    return ProcessStructuralAnalysis(
        analysis_version="0.1",
        process_id=process_id,
        process_name=process_name,
        process_version=process.process_version,
        handoffs=handoffs,
        handoff_candidates=candidates,
        rework_edges=rework_edges,
        paths=paths,
        step_classifications=classifications,
        unclassified_node_ids=unclassified,
        diagnostics=tuple(sorted(diagnostics, key=_diagnostic_sort_key)),
    )


def _analyze_handoffs(
    edges: list[Edge],
    *,
    nodes_by_id: dict[str, Node],
    diagnostics: list[StructuralDiagnostic],
) -> tuple[tuple[HandoffFinding, ...], tuple[HandoffFinding, ...]]:
    handoffs: list[HandoffFinding] = []
    candidates: list[HandoffFinding] = []
    for edge in sorted(edges, key=_edge_sort_key):
        source_lane = _node_lane(nodes_by_id.get(edge.source))
        target_lane = _node_lane(nodes_by_id.get(edge.target))
        if edge.handoff is True:
            handoffs.append(
                _handoff_finding(
                    edge,
                    classification="explicit",
                    source_lane=source_lane,
                    target_lane=target_lane,
                )
            )
            continue
        if edge.handoff is not None or not _is_cross_lane(source_lane, target_lane):
            continue
        candidates.append(
            _handoff_finding(
                edge,
                classification="candidate",
                source_lane=source_lane,
                target_lane=target_lane,
            )
        )
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-unmarked-lane-change",
                severity="warning",
                message=(
                    f"Lane change '{source_lane}' -> '{target_lane}' is not marked "
                    "as a handoff."
                ),
                source_id=edge.source,
                target_id=edge.target,
            )
        )
    return tuple(handoffs), tuple(candidates)


def _handoff_finding(
    edge: Edge,
    *,
    classification: HandoffClassification,
    source_lane: str | None,
    target_lane: str | None,
) -> HandoffFinding:
    metadata = edge.metadata or {}
    handoff_type = _optional_text(metadata.get("handoff_type"))
    return HandoffFinding(
        source_id=edge.source,
        target_id=edge.target,
        classification=classification,
        edge_id=edge.id,
        handoff_type=handoff_type,
        source_lane=source_lane,
        target_lane=target_lane,
    )


def _analyze_rework(
    edges: list[Edge],
    *,
    node_order: dict[str, int],
    diagnostics: list[StructuralDiagnostic],
) -> tuple[ReworkFinding, ...]:
    findings: list[ReworkFinding] = []
    for edge in sorted(edges, key=_edge_sort_key):
        classification = _rework_classification(edge, node_order=node_order)
        if classification is None:
            continue
        metadata = edge.metadata or {}
        findings.append(
            ReworkFinding(
                source_id=edge.source,
                target_id=edge.target,
                classification=classification,
                edge_id=edge.id,
                rate=_optional_number(metadata.get("rate")),
                reason=_optional_text(metadata.get("reason")),
                count=_optional_count(metadata.get("count")),
                frequency=_optional_text(metadata.get("frequency")),
            )
        )
        if classification == "inferred":
            diagnostics.append(
                StructuralDiagnostic(
                    code="structure-inferred-rework",
                    severity="info",
                    message="Backward edge is reported as inferred rework.",
                    source_id=edge.source,
                    target_id=edge.target,
                )
            )
    return tuple(findings)


def _rework_classification(
    edge: Edge, *, node_order: dict[str, int]
) -> ReworkClassification | None:
    edge_type = (edge.edge_type or "").strip().lower()
    if edge_type == "rework" or edge.rework is True:
        return "explicit"
    if edge.rework is False or edge_type:
        return None
    source_order = node_order.get(edge.source)
    target_order = node_order.get(edge.target)
    if (
        source_order is not None
        and target_order is not None
        and target_order <= source_order
    ):
        return "inferred"
    return None


def _analyze_paths(
    process: IR,
    *,
    primary_edges: tuple[Edge, ...],
    diagnostics: list[StructuralDiagnostic],
) -> tuple[StructuralPath, ...]:
    if any(node.type.strip().lower() in _PARALLEL_NODE_TYPES for node in process.nodes):
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-parallel-paths-unsupported",
                severity="warning",
                message=(
                    "Path length is unavailable for parallel split/join flow in "
                    "structural analysis 0.1."
                ),
            )
        )
        return ()

    adjacency = build_adjacency(process, edges=primary_edges)
    if has_cycle(adjacency):
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-cycle-unsupported",
                severity="warning",
                message=(
                    "Path length is unavailable because non-rework control flow "
                    "contains a cycle."
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
            StructuralDiagnostic(
                code="structure-invalid-boundary",
                severity="warning",
                message="Path analysis requires exactly one start and at least one end.",
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
            StructuralDiagnostic(
                code="structure-path-limit",
                severity="warning",
                message=(
                    "Path analysis stopped after the deterministic limit of "
                    f"{_MAX_PATHS} paths."
                ),
            )
        )
        return ()
    if not raw_paths:
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-no-complete-path",
                severity="warning",
                message="No complete non-rework start-to-end path was found.",
            )
        )
        return ()
    if len(raw_paths) > 1:
        diagnostics.append(
            StructuralDiagnostic(
                code="structure-multiple-paths",
                severity="info",
                message=f"Process has {len(raw_paths)} non-rework start-to-end paths.",
            )
        )
    return tuple(StructuralPath(node_ids=node_ids) for node_ids in raw_paths)


def _analyze_step_classification(
    nodes: list[Node],
) -> tuple[tuple[StepClassification, ...], tuple[str, ...]]:
    classifications: list[StepClassification] = []
    unclassified: list[str] = []
    for node in sorted(nodes, key=lambda item: item.id):
        node_type = node.type.strip().lower()
        value_class = _optional_text(extract_node_metadata(node).get("value_class"))
        classifications.append(
            StepClassification(
                node_id=node.id,
                node_type=node_type,
                value_class=value_class,
            )
        )
        if node_type in _CLASSIFIABLE_NODE_TYPES and value_class is None:
            unclassified.append(node.id)
    return tuple(classifications), tuple(unclassified)


def _classification_counts(values: Iterable[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts)}


def _node_lane(node: Node | None) -> str | None:
    attrs = node.attrs if node is not None else None
    return _optional_text(attrs.get("lane")) if isinstance(attrs, dict) else None


def _is_cross_lane(source_lane: str | None, target_lane: str | None) -> bool:
    return bool(source_lane and target_lane and source_lane != target_lane)


def _edge_sort_key(edge: Edge) -> tuple[str, str, str, str]:
    return edge.source, edge.target, edge.id or "", edge.outcome or ""


def _diagnostic_sort_key(
    diagnostic: StructuralDiagnostic,
) -> tuple[str, str, str, str, str]:
    return (
        diagnostic.code,
        diagnostic.node_id or "",
        diagnostic.source_id or "",
        diagnostic.target_id or "",
        diagnostic.message,
    )


def _identity_text(raw: object, fallback: str) -> str:
    normalized = _optional_text(raw)
    return normalized if normalized is not None else fallback


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _optional_number(value: object) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value)


def _optional_count(value: object) -> int | float | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return _optional_text(value)
