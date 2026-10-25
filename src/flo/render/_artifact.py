"""Backend-neutral render artifact contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from flo.diagnostics import DiagnosticReport, adapt_diagnostic, diagnostic_report


@dataclass(frozen=True)
class RenderArtifact:
    """Rendered artifact produced by a backend-neutral render entrypoint."""

    kind: str
    content: str
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def diagnostic_report(self) -> DiagnosticReport:
        """Expose operation findings without printing from programmatic rendering."""
        return artifact_diagnostic_report(self)


def artifact_diagnostic_report(
    artifact: RenderArtifact, *, diagram: str | None = None, strict: bool = False
) -> DiagnosticReport:
    """Preserve producer metadata and adapt legacy summary warnings once."""
    metadata = artifact.metadata
    if "operation_diagnostics" in metadata:
        return DiagnosticReport.from_dict(metadata["operation_diagnostics"])
    records = []
    context = {
        "artifact_kind": artifact.kind,
        "backend": artifact.backend,
        "diagram": diagram or metadata.get("diagram"),
        "strict": strict,
    }
    for key in ("render_diagnostics", "publication_diagnostics"):
        for item in metadata.get(key, ()):
            records.append(
                adapt_diagnostic(
                    item,
                    stage="render",
                    details={
                        **context,
                        "render_report": metadata.get("render_diagnostics_report", {}),
                    },
                )
            )
    known = {
        (item.code, item.message.removeprefix(f"{item.code}:").strip())
        for item in records
    }
    for message in str(metadata.get("warning") or "").splitlines():
        candidate = message.split(":", 1)[0] if ":" in message else ""
        code = candidate if re.fullmatch(r"[a-z][a-z0-9_-]+", candidate) else None
        if message and (code, message.removeprefix(f"{code}:").strip()) not in known:
            records.append(
                adapt_diagnostic(
                    {"code": code, "severity": "warning", "message": message},
                    stage="render",
                    details={
                        **context,
                        "projection_diagnostics": metadata.get(
                            "projection_diagnostics", ()
                        ),
                    },
                )
            )
    return diagnostic_report(records)
