"""Canonical process intermediate representation and validation contracts."""

from .enums import LaneType, NodeKind, ProcessValueClass, ValueClass
from .models import IR, Node
from .validate import ensure_schema_aligned, validate_ir

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
