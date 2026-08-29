"""Exporter option types for machine-readable projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

ExportFormat = Literal["json", "ingredients", "movement"]
ExportProfile = Literal["default"]


@dataclass(frozen=True)
class ExportOptions:
    """Configuration for exporter registry dispatch.

    The exporter layer is intentionally separate from renderers: exporter
    outputs are machine-readable contract projections.
    """

    export_format: ExportFormat = "json"
    profile: ExportProfile = "default"
    indent: int = 2

    @classmethod
    def from_mapping(cls, options: Mapping[str, Any] | None) -> "ExportOptions":
        """Create normalized export options from CLI/core option mappings."""
        if not options:
            return cls()

        export_format_raw = str(options.get("export") or "json").strip().lower()
        profile_raw = str(options.get("export_profile") or "default").strip().lower()
        indent_raw = options.get("json_indent", 2)

        if export_format_raw == "ingredients":
            export_format: ExportFormat = "ingredients"
        elif export_format_raw == "movement":
            export_format = "movement"
        else:
            export_format = "json"
        profile: ExportProfile = "default" if profile_raw == "default" else "default"

        try:
            indent = int(indent_raw)
        except Exception:
            indent = 2
        indent = 2 if indent < 0 else indent

        return cls(export_format=export_format, profile=profile, indent=indent)
