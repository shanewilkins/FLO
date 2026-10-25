"""Adapt artifact-owned findings into the shared operation delivery envelope."""

from dataclasses import replace

from flo.diagnostics import diagnostic_report
from flo.process.analysis.diagnostics import timing_diagnostic_report
from flo.process.ir.models import IR

from ._artifact import RenderArtifact, artifact_diagnostic_report


def attach_operation_diagnostics(
    artifact: RenderArtifact,
    process,
    *,
    diagram: str | None = None,
    strict: bool = False,
) -> RenderArtifact:
    """Attach a report without modifying the rendered bytes or canonical input."""
    findings = list(
        artifact_diagnostic_report(artifact, diagram=diagram, strict=strict).diagnostics
    )
    if isinstance(process, IR):
        findings.extend(timing_diagnostic_report(process).diagnostics)
    report = diagnostic_report(findings)
    return replace(
        artifact,
        metadata={**artifact.metadata, "operation_diagnostics": report.as_dict()},
    )
