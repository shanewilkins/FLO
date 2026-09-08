"""User-facing presentation of typed FLO analysis results."""

from __future__ import annotations

import json
from math import isfinite

from flo.process.analysis import (
    ModelInspectionReport,
    ProcessStructuralAnalysis,
    ProcessTimingAnalysis,
    StructuralDiagnostic,
)


def format_timing_analysis(
    result: ProcessTimingAnalysis,
    *,
    output_format: str = "text",
) -> str:
    """Format one timing-analysis result for humans or deterministic tooling."""
    if output_format == "json":
        return json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
    if output_format != "text":
        raise ValueError(f"unsupported inspect format: {output_format}")
    return _format_timing_text(result)


def format_structural_analysis(
    result: ProcessStructuralAnalysis,
    *,
    output_format: str = "text",
) -> str:
    """Format one structural-analysis result for humans or tooling."""
    if output_format == "json":
        return json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
    if output_format != "text":
        raise ValueError(f"unsupported inspect format: {output_format}")
    return _format_structural_text(result)


def format_model_inspection(
    report: ModelInspectionReport,
    *,
    output_format: str = "text",
) -> str:
    """Format one model-inspection report for humans or tooling."""
    if output_format == "json":
        return json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"
    if output_format != "text":
        raise ValueError(f"unsupported inspect format: {output_format}")
    return _format_model_inspection_text(report)


def _format_timing_text(result: ProcessTimingAnalysis) -> str:
    process_label = result.process_name
    if result.process_id != result.process_name:
        process_label = f"{process_label} ({result.process_id})"

    totals = result.declared_totals
    lines = [
        f"Process: {process_label}",
        f"Version: {result.process_version if result.process_version is not None else '-'}",
        f"Timing coverage: {'complete' if result.timing_complete else 'incomplete'}",
        "",
        "Declared totals:",
        f"  Cycle time: {_format_duration(totals.cycle_time_seconds)}",
        f"  Wait time: {_format_duration(totals.wait_time_seconds)}",
        f"  Changeover time: {_format_duration(totals.changeover_time_seconds)}",
        f"  Elapsed subtotal: {_format_duration(totals.elapsed_time_seconds)}",
        "",
        f"Modeled lead time: {_format_modeled_lead_time(result)}",
        f"Paths analyzed: {len(result.paths)}",
        f"Changeover policy: {_humanize_policy(result.changeover_exposure_policy)}",
    ]

    if result.diagnostics:
        lines.extend(("", "Diagnostics:"))
        for diagnostic in result.diagnostics:
            location = f" ({diagnostic.node_id})" if diagnostic.node_id else ""
            lines.append(
                f"  [{diagnostic.severity}] {diagnostic.code}{location}: "
                f"{diagnostic.message}"
            )

    return "\n".join(lines) + "\n"


def _format_structural_text(result: ProcessStructuralAnalysis) -> str:
    process_label = result.process_name
    if result.process_id != result.process_name:
        process_label = f"{process_label} ({result.process_id})"

    path_range = "unavailable"
    if result.minimum_path_edge_count is not None:
        path_range = str(result.minimum_path_edge_count)
        if result.maximum_path_edge_count != result.minimum_path_edge_count:
            path_range = (
                f"{result.minimum_path_edge_count} to {result.maximum_path_edge_count}"
            )

    lines = [
        f"Process: {process_label}",
        f"Version: {result.process_version if result.process_version is not None else '-'}",
        "",
        "Structural summary:",
        f"  Explicit handoffs: {len(result.handoffs)}",
        f"  Handoff candidates: {len(result.handoff_candidates)}",
        f"  Rework edges: {len(result.rework_edges)}",
        f"  Non-rework paths: {len(result.paths)}",
        f"  Path length (edges): {path_range}",
        "",
        "Step classification:",
        f"  Node kinds: {_format_counts(result.node_type_counts)}",
        f"  Value classes: {_format_counts(result.value_class_counts)}",
        f"  Unclassified steps: {_format_ids(result.unclassified_node_ids)}",
    ]

    if result.diagnostics:
        lines.extend(("", "Diagnostics:"))
        for diagnostic in result.diagnostics:
            lines.append(
                f"  [{diagnostic.severity}] {diagnostic.code}"
                f"{_structural_diagnostic_location(diagnostic)}: "
                f"{diagnostic.message}"
            )
    return "\n".join(lines) + "\n"


def _format_model_inspection_text(report: ModelInspectionReport) -> str:
    process_label = report.process_name
    if report.process_id != report.process_name:
        process_label = f"{process_label} ({report.process_id})"
    composition = report.composition
    lines = [
        f"Process: {process_label}",
        f"Version: {report.process_version if report.process_version is not None else '-'}",
        "Validation: valid",
        "",
        "Composition:",
        f"  Entry source: {composition.entry_source}",
        f"  Includes: {_format_ids(composition.included_sources)}",
        "",
        "Model summary:",
        f"  Nodes: {report.node_count}",
        f"  Edges: {report.edge_count}",
        f"  Lanes: {len(report.lane_ids)}",
        f"  Paths: {len(report.structure.paths)}",
        "",
        "Entities:",
        f"  Items: {len(report.entities.item_ids)}",
        f"  Resources: {len(report.entities.resource_ids)}",
        f"  Locations: {len(report.entities.location_ids)}",
        "",
        f"Views: {', '.join(view.view_id for view in report.views)}",
    ]
    if report.readiness:
        lines.extend(("", "Requested readiness:"))
        for readiness in report.readiness:
            lines.append(
                f"  {readiness.target_type} {readiness.target}: {readiness.status}"
            )
            for finding in readiness.findings:
                ids = f" ({', '.join(finding.ids)})" if finding.ids else ""
                lines.append(
                    f"    [{finding.kind}] {finding.code}{ids}: {finding.message}"
                )
    if report.structure.diagnostics:
        lines.extend(("", "Model diagnostics:"))
        for diagnostic in report.structure.diagnostics:
            lines.append(
                f"  [{diagnostic.severity}] {diagnostic.code}: {diagnostic.message}"
            )
    return "\n".join(lines) + "\n"


def _format_modeled_lead_time(result: ProcessTimingAnalysis) -> str:
    if result.modeled_lead_time_seconds is not None:
        return _format_duration(result.modeled_lead_time_seconds)

    minimum = result.minimum_path_lead_time_seconds
    maximum = result.maximum_path_lead_time_seconds
    if minimum is not None and maximum is not None:
        return (
            f"{_format_duration(minimum)} to {_format_duration(maximum)} "
            f"across {len(result.paths)} paths"
        )
    return "unavailable"


def _format_duration(seconds: float | None) -> str:
    if seconds is None or not isfinite(seconds):
        return "unavailable"
    if seconds == 0:
        return "0 min"
    if seconds % 60 == 0:
        return f"{_format_number(seconds / 60)} min"
    return f"{_format_number(seconds)} s"


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _humanize_policy(policy: str) -> str:
    if policy == "one_declared_changeover_per_visited_step":
        return "one declared changeover per visited step"
    return policy.replace("_", " ")


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _format_ids(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "none"


def _structural_diagnostic_location(diagnostic: StructuralDiagnostic) -> str:
    source_id = diagnostic.source_id
    target_id = diagnostic.target_id
    if source_id and target_id:
        return f" ({source_id} -> {target_id})"
    node_id = diagnostic.node_id
    return f" ({node_id})" if node_id else ""
