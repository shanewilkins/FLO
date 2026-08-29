"""User-facing presentation of typed FLO analysis results."""

from __future__ import annotations

import json
from math import isfinite

from flo.process.analysis import ProcessTimingAnalysis


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


def _format_duration(seconds: float) -> str:
    if not isfinite(seconds):
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
