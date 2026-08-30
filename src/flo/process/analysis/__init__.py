"""Deterministic analyses over canonical process IR."""

from .scc import scc_condense
from .movement import (
    infer_material_movements,
    aggregate_material_movements,
    infer_people_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
)
from .process_metadata import extract_process_metadata
from .timing import (
    NodeTiming,
    ProcessTimingAnalysis,
    TimingDiagnostic,
    TimingPath,
    TimingTotals,
    analyze_process_timing,
)
from .structure import (
    HandoffFinding,
    ProcessStructuralAnalysis,
    ReworkFinding,
    StepClassification,
    StructuralDiagnostic,
    StructuralPath,
    analyze_process_structure,
)
from .inspection import (
    EntitySummary,
    ModelInspectionReport,
    NamedViewSummary,
    ProjectionReadiness,
    ReadinessFinding,
    SourceCompositionSummary,
    inspect_process_model,
)
from .value_stream import (
    ValueStreamDiagnostic,
    ValueStreamFlow,
    ValueStreamNode,
    ValueStreamProjection,
    project_value_stream,
)

__all__ = [
    "scc_condense",
    "infer_material_movements",
    "aggregate_material_movements",
    "infer_people_movements",
    "aggregate_people_movements",
    "aggregate_people_movements_by_worker",
    "extract_location_spatial_index",
    "extract_process_metadata",
    "NodeTiming",
    "ProcessTimingAnalysis",
    "TimingDiagnostic",
    "TimingPath",
    "TimingTotals",
    "analyze_process_timing",
    "HandoffFinding",
    "ProcessStructuralAnalysis",
    "ReworkFinding",
    "StepClassification",
    "StructuralDiagnostic",
    "StructuralPath",
    "analyze_process_structure",
    "EntitySummary",
    "ModelInspectionReport",
    "NamedViewSummary",
    "ProjectionReadiness",
    "ReadinessFinding",
    "SourceCompositionSummary",
    "inspect_process_model",
    "ValueStreamDiagnostic",
    "ValueStreamFlow",
    "ValueStreamNode",
    "ValueStreamProjection",
    "project_value_stream",
]
