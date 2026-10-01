"""Supported Python integration facade for FLO source operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flo.process.analysis import ModelInspectionReport, inspect_process_model
from flo.process.export import export_ir
from flo.process.ir import IR, validate_ir
from flo.source import compile_adapter, parse_adapter, pop_source_composition
from flo.source.diagnostics import SourceDiagnostic, source_diagnostic


@dataclass(frozen=True)
class OperationResult[ResultValue]:
    """Typed result for a public FLO operation without raised domain errors."""

    value: ResultValue | None
    diagnostics: tuple[SourceDiagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        """Return whether the operation completed without diagnostics."""
        return self.value is not None and not self.diagnostics


def parse(
    content: str, *, source_path: str | None = None
) -> OperationResult[dict[str, Any]]:
    """Parse FLO source into the compiler-facing mapping contract."""
    try:
        return OperationResult(value=parse_adapter(content, source_path=source_path))
    except Exception as exc:
        return _failure(content=content, source_path=source_path, error=exc)


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
        return _failure(content=content, source_path=source_path, error=exc)


def validate(content: str, *, source_path: str | None = None) -> OperationResult[IR]:
    """Compile and semantically validate FLO source into canonical IR."""
    compiled = compile(content, source_path=source_path)
    if not compiled.ok:
        return OperationResult(value=None, diagnostics=compiled.diagnostics)
    try:
        validate_ir(compiled.value)
    except Exception as exc:
        return _failure(content=content, source_path=source_path, error=exc)
    return compiled


def inspect(
    content: str, *, source_path: str | None = None
) -> OperationResult[ModelInspectionReport]:
    """Validate FLO source and return its model-inspection report."""
    parsed = parse(content, source_path=source_path)
    if not parsed.ok:
        return OperationResult(value=None, diagnostics=parsed.diagnostics)
    value = parsed.value
    if value is None:
        return OperationResult(value=None, diagnostics=parsed.diagnostics)
    composition = pop_source_composition(value, source_path=source_path)
    try:
        process = compile_adapter(value)
        validate_ir(process)
        return OperationResult(
            value=inspect_process_model(
                process,
                entry_source=composition.entry_source,
                included_sources=composition.included_sources,
            )
        )
    except Exception as exc:
        return _failure(content=content, source_path=source_path, error=exc)


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
            value=export_ir(validated.value, {"export": export_format})
        )
    except Exception as exc:
        return _failure(content=content, source_path=source_path, error=exc)


def _failure(
    *, content: str, source_path: str | None, error: BaseException
) -> OperationResult[Any]:
    diagnostic = source_diagnostic(
        str(error), content=content, source_path=source_path, cause=error
    )
    return OperationResult(value=None, diagnostics=(diagnostic,))


__all__ = ["OperationResult", "compile", "export", "inspect", "parse", "validate"]
