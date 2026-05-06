"""JSON projection helpers for canonical FLO IR."""

from __future__ import annotations

import json

from flo.compiler.ir.schema_projection import ir_to_schema_dict
from flo.compiler.ir.models import IR


def ir_to_schema_json(ir: IR, *, indent: int | None = 2) -> str:
    """Serialize in-memory IR as schema-shaped JSON export text."""
    payload = ir_to_schema_dict(ir)
    if indent is None or int(indent) <= 0:
        return json.dumps(payload, separators=(",", ":"))
    return json.dumps(payload, indent=int(indent))
