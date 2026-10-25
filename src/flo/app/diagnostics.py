"""Application operation results over the common diagnostic envelope."""

from dataclasses import dataclass, field

from flo.diagnostics import Diagnostic, DiagnosticReport, diagnostic_report


@dataclass(frozen=True)
class CommandResult:
    """One command payload, exit status and operation-owned findings."""

    exit_code: int
    output: str
    report: DiagnosticReport = field(default_factory=DiagnosticReport)

    def as_tuple(self) -> tuple[int, str, str]:
        """Retain the legacy run_content result without a report side channel."""
        return self.exit_code, self.output, self.report.text()

    @classmethod
    def from_legacy(cls, code: int, output: str, message: str) -> CommandResult:
        """Adapt an existing command producer while preserving its message/code."""
        if not message:
            return cls(code, output)
        partial = message.startswith(
            ("spaghetti-missing-spatial:", "value-stream-partial:")
        )
        stage = (
            "run_content"
            if code
            else "partial_render"
            if partial
            else "fail_open_fallback"
        )
        record = Diagnostic(
            code=None,
            severity="error" if code else "warning",
            message=message,
            stage=stage,
        )
        return cls(code, output, diagnostic_report((record,)))
