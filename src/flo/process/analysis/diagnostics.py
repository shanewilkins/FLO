"""Adapt existing analysis findings and aggregate applicable missing timing."""

from flo.diagnostics import (
    Diagnostic,
    DiagnosticReport,
    adapt_diagnostic,
    diagnostic_report,
)
from flo.process.ir.models import IR

from .timing import ProcessTimingAnalysis, analyze_process_timing


def timing_diagnostic_report(
    process: IR, result: ProcessTimingAnalysis | None = None
) -> DiagnosticReport:
    """Collect timing evidence without changing arithmetic, strictness, or the IR."""
    analysis = result or analyze_process_timing(process)
    nodes = {node.id: node for node in process.nodes}
    missing = []
    for timing in analysis.node_timings:
        applicable = ("wait_time",) if timing.node_type in {"queue", "wait"} else ()
        if timing.node_type in {"task", "system_task", "subprocess"}:
            applicable = ("cycle_time", "wait_time")
            if timing.changeover_source_field is None:
                applicable += ("changeover_time",)
        missing.extend(
            {
                "node_id": timing.node_id,
                "field": name,
                "field_path": f"nodes.{timing.node_id}.{name}",
            }
            for name in applicable
            if getattr(nodes[timing.node_id], name) is None
        )
    records = [
        adapt_diagnostic(item, stage="analysis.timing")
        for item in analysis.diagnostics
        if item.code != "timing-incomplete" or not missing
    ]
    if missing:
        node_ids = sorted({item["node_id"] for item in missing})
        records.append(
            Diagnostic(
                code="timing-incomplete",
                severity="warning",
                stage="analysis.timing",
                message=f"{len(missing)} unmeasured timing field(s) across {len(node_ids)} step(s); processing, waiting or setup values remain unknown.",
                suggestion="Declare measured durations with explicit units; retain omission for unmeasured values.",
                details={"affected_node_ids": node_ids, "missing_fields": missing},
            )
        )
    return diagnostic_report(records)


def analysis_diagnostic_report(result, *, stage: str) -> DiagnosticReport:
    """Keep the full native analysis diagnostic fields in operation delivery."""
    return diagnostic_report(
        adapt_diagnostic(item, stage=stage) for item in result.diagnostics
    )
