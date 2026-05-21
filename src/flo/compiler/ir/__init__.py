"""IR package nested under the compiler layer.

This package mirrors the previous `flo.ir` package but lives under
`flo.compiler.ir` to keep top-level `src/flo/` tidy.
"""

from .models import IR, Node
from .schema_projection import ir_to_schema_dict
from .validate import validate_ir, ensure_schema_aligned
from .enums import NodeKind, LaneType, ValueClass, ProcessValueClass

__all__ = [
    "IR",
    "Node",
    "ir_to_schema_dict",
    "validate_ir",
    "ensure_schema_aligned",
    "NodeKind",
    "LaneType",
    "ValueClass",
    "ProcessValueClass",
]
