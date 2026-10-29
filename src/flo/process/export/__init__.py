"""Export projections for canonical FLO IR."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .items_export import ir_to_items_text
from .json_export import ir_to_schema_json
from .movement_export import ir_to_movement_text
from .options import ExportOptions

_Exporter = Callable[[Any, ExportOptions], str]


def _json_exporter(ir: Any, options: ExportOptions) -> str:
    return ir_to_schema_json(ir, indent=options.indent)


def _items_exporter(ir: Any, options: ExportOptions) -> str:
    return ir_to_items_text(ir)


def _movement_exporter(ir: Any, options: ExportOptions) -> str:
    return ir_to_movement_text(ir)


_EXPORTERS: dict[str, _Exporter] = {
    "json": _json_exporter,
    "items": _items_exporter,
    "movement": _movement_exporter,
}


def export_ir(ir: Any, options: dict | None = None) -> str:
    """Export IR using exporter registry based on export options."""
    export_options = ExportOptions.from_mapping(options)
    exporter = _EXPORTERS[export_options.export_format]
    return exporter(ir, export_options)


__all__ = ["ExportOptions", "export_ir"]
