"""Supported Python integration facade for FLO source operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.app import prepare_source
from flo.diagnostics import (
    Diagnostic,
    DiagnosticReport,
    adapt_diagnostic,
    diagnostic_report,
)
from flo.process.analysis import ModelInspectionReport, inspect_process_model
from flo.process.analysis.diagnostics import (
    analysis_diagnostic_report,
    timing_diagnostic_report,
)
from flo.process.export import export_ir
from flo.process.ir import IR
from flo.source import compile_adapter, parse_adapter
from flo.source.diagnostics import SourceDiagnostic, source_diagnostic


@dataclass(frozen=True)
class OperationResult[ResultValue]:
    """Typed result for a public FLO operation without raised domain errors."""

    value: ResultValue | None
    diagnostics: tuple[Diagnostic | SourceDiagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        """Return whether a value exists and no error-severity finding occurred."""
        return self.value is not None and not any(
            item.severity == "error" for item in self.diagnostics
        )

    @property
    def report(self) -> DiagnosticReport:
        """Expose the same normalized operation report as CLI/artifact consumers."""
        return diagnostic_report(
            item
            if isinstance(item, Diagnostic)
            else adapt_diagnostic(item, stage="source")
            for item in self.diagnostics
        )


def parse(
    content: str, *, source_path: str | None = None
) -> OperationResult[dict[str, Any]]:
    """Parse FLO source into the compiler-facing mapping contract."""
    try:
        return OperationResult(value=parse_adapter(content, source_path=source_path))
    except Exception as exc:
        return _failure(
            content=content, source_path=source_path, error=exc, stage="parse"
        )


def compile(content: str, *, source_path: str | None = None) -> OperationResult[IR]:
    """Compile FLO source into canonical IR without semantic validation."""
    parsed = parse(content, source_path=source_path)
    if not parsed.ok:
        return OperationResult(value=None, diagnostics=parsed.diagnostics)
    value = parsed.value
    if value is None:
        return OperationResult(value=None, diagnostics=parsed.diagnostics)
    try:
        return OperationResult(value=compile_adapter(value))
    except Exception as exc:
        return _failure(
            content=content, source_path=source_path, error=exc, stage="compile"
        )


def validate(content: str, *, source_path: str | None = None) -> OperationResult[IR]:
    """Compile and semantically validate FLO source into canonical IR."""
    try:
        process, _composition = prepare_source(content, source_path=source_path)
    except Exception as exc:
        return _failure(
            content=content, source_path=source_path, error=exc, stage="validate"
        )
    return OperationResult(
        value=process,
        diagnostics=timing_diagnostic_report(process)
        .with_source(source_path)
        .diagnostics,
    )


def inspect(
    content: str, *, source_path: str | None = None
) -> OperationResult[ModelInspectionReport]:
    """Validate FLO source and return its model-inspection report."""
    try:
        process, composition = prepare_source(content, source_path=source_path)
        report = inspect_process_model(
            process,
            entry_source=composition.entry_source,
            included_sources=composition.included_sources,
        )
        findings = diagnostic_report(
            (
                *timing_diagnostic_report(process).diagnostics,
                *analysis_diagnostic_report(
                    report.structure, stage="analysis.structure"
                ).diagnostics,
            )
        )
        return OperationResult(
            value=report, diagnostics=findings.with_source(source_path).diagnostics
        )
    except Exception as exc:
        return _failure(
            content=content, source_path=source_path, error=exc, stage="inspect"
        )


def export(
    content: str,
    *,
    source_path: str | None = None,
    export_format: str = "json",
) -> OperationResult[str]:
    """Validate FLO source and export a deterministic supported projection."""
    validated = validate(content, source_path=source_path)
    if not validated.ok:
        return OperationResult(value=None, diagnostics=validated.diagnostics)
    try:
        return OperationResult(
            value=export_ir(validated.value, {"export": export_format}),
            diagnostics=validated.diagnostics,
        )
    except Exception as exc:
        return _failure(
            content=content,
            source_path=source_path,
            error=exc,
            stage="export",
            previous=validated.report.diagnostics,
        )


def _failure(
    *,
    content: str,
    source_path: str | None,
    error: BaseException,
    stage: str,
    previous: tuple[Diagnostic, ...] = (),
) -> OperationResult[Any]:
    diagnostic = getattr(error, "diagnostic", None) or source_diagnostic(
        str(error), content=content, source_path=source_path, cause=error
    )
    record = adapt_diagnostic(
        diagnostic, stage=getattr(error, "error_stage", None) or stage
    )
    return OperationResult(
        value=None, diagnostics=diagnostic_report((*previous, record)).diagnostics
    )


__all__ = ["OperationResult", "compile", "export", "inspect", "parse", "validate"]
