"""Shared render diagnostic contracts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import structlog
from structlog.stdlib import BoundLogger

RenderDiagnosticSeverity = Literal["warning", "error"]


@dataclass(frozen=True)
class RenderDiagnostic:
    """A structured render-time warning or error."""

    code: str
    severity: RenderDiagnosticSeverity
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderDiagnosticsReport:
    """Operation-level summary above raw render diagnostic events."""

    diagram: str
    backend: str
    artifact_kind: str
    strict: bool = False
    diagnostics: tuple[RenderDiagnostic, ...] = ()
    warning_count: int = 0
    error_count: int = 0
    code_counts: dict[str, int] = field(default_factory=dict)
    category_counts: dict[str, int] = field(default_factory=dict)
    partial_output: bool = False
    summary: str = ""


def build_render_diagnostics_report(
    diagnostics: tuple[RenderDiagnostic, ...],
    *,
    diagram: str,
    backend: str,
    artifact_kind: str,
    strict: bool = False,
) -> RenderDiagnosticsReport:
    """Build a thin operation-level report from raw render diagnostics."""
    warning_count = sum(
        1 for diagnostic in diagnostics if diagnostic.severity == "warning"
    )
    error_count = sum(1 for diagnostic in diagnostics if diagnostic.severity == "error")
    code_counts = dict(Counter(diagnostic.code for diagnostic in diagnostics))
    category_counts = dict(
        Counter(
            classify_render_diagnostic_code(diagnostic.code)
            for diagnostic in diagnostics
        )
    )
    partial_output = any(
        category in {"missing_geometry", "lossy_recovery"}
        for category in category_counts
    )
    if error_count:
        summary = (
            f"{error_count} error(s), {warning_count} warning(s) while rendering "
            f"{diagram} via {backend}"
        )
    elif warning_count:
        summary = f"{warning_count} warning(s) while rendering {diagram} via {backend}"
    else:
        summary = f"No render diagnostics for {diagram} via {backend}"
    return RenderDiagnosticsReport(
        diagram=diagram,
        backend=backend,
        artifact_kind=artifact_kind,
        strict=strict,
        diagnostics=diagnostics,
        warning_count=warning_count,
        error_count=error_count,
        code_counts=code_counts,
        category_counts=category_counts,
        partial_output=partial_output,
        summary=summary,
    )


def classify_render_diagnostic_code(code: str) -> str:
    """Map a low-level diagnostic code to a report-level category."""
    normalized = str(code or "").strip().lower()
    if "namespace" in normalized or "reserved" in normalized:
        return "namespace_collision"
    if normalized in {
        "elk-edge-endpoints-missing",
        "elk-edge-geometry-missing",
        "elk-edge-missing",
        "elk-lane-frame-missing",
    }:
        return "missing_geometry"
    if normalized in {
        "elk-edge-container-unknown",
        "elk-edge-unexpected",
        "publication-fallback",
    }:
        return "lossy_recovery"
    return "uncategorized"


def serialize_render_diagnostics(
    diagnostics: tuple[RenderDiagnostic, ...],
) -> list[dict[str, Any]]:
    """Return diagnostics as artifact-friendly metadata records."""
    return [
        {
            "code": diagnostic.code,
            "severity": diagnostic.severity,
            "message": diagnostic.message,
            **diagnostic.metadata,
        }
        for diagnostic in diagnostics
    ]


def serialize_render_diagnostics_report(
    report: RenderDiagnosticsReport,
) -> dict[str, Any]:
    """Return a report as artifact-friendly metadata."""
    return {
        "diagram": report.diagram,
        "backend": report.backend,
        "artifact_kind": report.artifact_kind,
        "strict": report.strict,
        "warning_count": report.warning_count,
        "error_count": report.error_count,
        "diagnostic_count": len(report.diagnostics),
        "code_counts": dict(sorted(report.code_counts.items())),
        "category_counts": dict(sorted(report.category_counts.items())),
        "partial_output": report.partial_output,
        "summary": report.summary,
        "diagnostics": serialize_render_diagnostics(report.diagnostics),
    }


def log_render_diagnostics(
    report: RenderDiagnosticsReport,
    logger: BoundLogger | None = None,
) -> None:
    """Emit structured render diagnostics through the shared logger."""
    if not report.diagnostics:
        return
    active_logger = logger or cast(BoundLogger, structlog.get_logger())
    bound_logger = active_logger.bind(
        component="render",
        diagram=report.diagram,
        backend=report.backend,
        artifact_kind=report.artifact_kind,
        strict=report.strict,
        warning_count=report.warning_count,
        error_count=report.error_count,
        partial_output=report.partial_output,
    )
    bound_logger.info(
        "render_diagnostics_summary",
        message=report.summary,
        diagnostic_count=len(report.diagnostics),
        code_counts=dict(sorted(report.code_counts.items())),
        category_counts=dict(sorted(report.category_counts.items())),
    )
    for diagnostic in report.diagnostics:
        log_method = (
            bound_logger.error
            if diagnostic.severity == "error"
            else bound_logger.warning
        )
        log_method(
            "render_diagnostic",
            message=diagnostic.message,
            code=diagnostic.code,
            severity=diagnostic.severity,
            **diagnostic.metadata,
        )
