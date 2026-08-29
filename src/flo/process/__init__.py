"""Stable process-domain contracts, validation, analysis, and serialization."""

from __future__ import annotations

from .ir import (
    IR,
    LaneType,
    Node,
    NodeKind,
    ProcessValueClass,
    ValueClass,
    ensure_schema_aligned,
    validate_ir,
)

__all__ = [
    "IR",
    "LaneType",
    "Node",
    "NodeKind",
    "ProcessValueClass",
    "ValueClass",
    "ensure_schema_aligned",
    "validate_ir",
]
