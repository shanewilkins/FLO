"""Deterministic analyses over canonical process IR."""

from .inspection import (
    EntitySummary,
    ModelInspectionReport,
    NamedViewSummary,
    ProjectionReadiness,
    ReadinessFinding,
    SourceCompositionSummary,
    inspect_process_model,
)
from .movement import (
    aggregate_material_movements,
    aggregate_people_movements,
    aggregate_people_movements_by_worker,
    extract_location_spatial_index,
    infer_material_movements,
    infer_people_movements,
)
from .process_metadata import extract_process_metadata
from .scc import scc_condense
from .structure import (
    HandoffFinding,
    ProcessStructuralAnalysis,
    ReworkFinding,
    StepClassification,
    StructuralDiagnostic,
    StructuralPath,
    analyze_process_structure,
)
from .timing import (
    NodeTiming,
    ProcessTimingAnalysis,
    TimingDiagnostic,
    TimingPath,
    TimingTotals,
    analyze_process_timing,
)
from .value_stream import (
    ValueStreamDiagnostic,
    ValueStreamFlow,
    ValueStreamNode,
    ValueStreamProjection,
    project_value_stream,
)

__all__ = [
    "EntitySummary",
    "HandoffFinding",
    "ModelInspectionReport",
    "NamedViewSummary",
    "NodeTiming",
    "ProcessStructuralAnalysis",
    "ProcessTimingAnalysis",
    "ProjectionReadiness",
    "ReadinessFinding",
    "ReworkFinding",
    "SourceCompositionSummary",
    "StepClassification",
    "StructuralDiagnostic",
    "StructuralPath",
    "TimingDiagnostic",
    "TimingPath",
    "TimingTotals",
    "ValueStreamDiagnostic",
    "ValueStreamFlow",
    "ValueStreamNode",
    "ValueStreamProjection",
    "aggregate_material_movements",
    "aggregate_people_movements",
    "aggregate_people_movements_by_worker",
    "analyze_process_structure",
    "analyze_process_timing",
    "extract_location_spatial_index",
    "extract_process_metadata",
    "infer_material_movements",
    "infer_people_movements",
    "inspect_process_model",
    "project_value_stream",
    "scc_condense",
]
