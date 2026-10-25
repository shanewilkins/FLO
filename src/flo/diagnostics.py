"""Architecture-neutral diagnostic records and deterministic operation reports."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields, is_dataclass, replace
from typing import Any, Literal

Severity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class Diagnostic:
    """Delivery envelope preserving source context and producer-specific evidence."""

    code: str | None
    severity: Severity
    message: str
    stage: str
    source: str | None = None
    line: int | None = None
    column: int | None = None
    excerpt: str | None = None
    field_path: str | None = None
    suggestion: str | None = None
    include_chain: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        """Render a record using the existing compiler-style source convention."""
        return render_diagnostic(self)


@dataclass(frozen=True)
class DiagnosticReport:
    """One deduplicated report, shared by CLI, API, and artifact delivery."""

    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def error_count(self) -> int:
        """Count fatal findings without promoting warnings."""
        return sum(item.severity == "error" for item in self.diagnostics)

    @property
    def warning_count(self) -> int:
        """Count actionable warning records after aggregation."""
        return sum(item.severity == "warning" for item in self.diagnostics)

    def as_dict(self) -> dict[str, Any]:
        """Return the versioned, JSON-compatible report envelope."""
        return {
            "report_version": "0.1",
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": sum(item.severity == "info" for item in self.diagnostics),
            "diagnostics": [asdict(item) for item in self.diagnostics],
        }

    def text(self, *, include_info: bool = False, prefixes: bool = False) -> str:
        """Format concise delivery text without exposing full producer payloads."""
        lines = []
        for item in self.diagnostics:
            if item.severity == "info" and not include_info:
                continue
            message = item.message
            if item.code and not message.startswith(f"{item.code}:"):
                message = f"{item.code}: {message}"
            prefix = f"{item.severity.capitalize()}: " if prefixes else ""
            lines.append(prefix + message)
        return "\n".join(lines)

    def with_source(self, source: str | None) -> DiagnosticReport:
        """Attach operation context without replacing producer-owned locations."""
        source = "<stdin>" if source == "-" else source
        return diagnostic_report(
            replace(item, source=item.source or source) for item in self.diagnostics
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DiagnosticReport:
        """Read an artifact-owned report without aliasing its mutable metadata."""
        return diagnostic_report(
            Diagnostic(**deepcopy(item)) for item in value.get("diagnostics", ())
        )


def adapt_diagnostic(record: Any, *, stage: str, **context: Any) -> Diagnostic:
    """Adapt existing dataclass/mapping producers without coupling them to delivery."""
    raw = asdict(record) if is_dataclass(record) else deepcopy(dict(record))
    raw.update(deepcopy(context))
    raw.pop("stage", None)
    common = {item.name for item in fields(Diagnostic)} - {"stage", "details"}
    values = {name: raw.pop(name) for name in tuple(raw) if name in common}
    details = raw.pop("details", {})
    return Diagnostic(stage=stage, **values, details={**details, **raw})


def diagnostic_report(items: Iterable[Diagnostic] = ()) -> DiagnosticReport:
    """Order deterministically and emit an equivalent finding only once."""
    ordered = sorted(
        items,
        key=lambda item: (
            {"error": 0, "warning": 1, "info": 2}[item.severity],
            item.stage,
            item.code or "",
            item.source or "",
            item.field_path or "",
            json.dumps(asdict(item), sort_keys=True),
        ),
    )
    unique: dict[str, Diagnostic] = {}
    for item in ordered:
        identity = asdict(item)
        identity.pop("stage")
        unique.setdefault(json.dumps(identity, sort_keys=True), item)
    return DiagnosticReport(tuple(unique.values()))


def render_diagnostic(item: Any) -> str:
    """Render common located fields for both source and operation records."""
    if (
        item.source is None
        or item.line is None
        or item.column is None
        or item.excerpt is None
    ):
        return item.message
    location = f"{item.source}:{item.line}:{item.column}"
    suffix = f" [{item.field_path}]" if item.field_path else ""
    gutter = str(item.line)
    padding = " " * max(0, item.column - 1)
    return "\n".join(
        (
            f"{location}: {item.message}{suffix}",
            f"  {gutter} | {item.excerpt}",
            f"  {' ' * len(gutter)} | {padding}^",
        )
    )
