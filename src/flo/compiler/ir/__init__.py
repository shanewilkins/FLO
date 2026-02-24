"""IR package nested under the compiler layer.

This package mirrors the previous `flo.ir` package but lives under
`flo.compiler.ir` to keep top-level `src/flo/` tidy.
"""
from .models import IR, Node
from .validate import validate_ir, ensure_schema_aligned
from .enums import NodeKind, LaneType, ValueClass

__all__ = [
	"IR",
	"Node",
	"validate_ir",
	"ensure_schema_aligned",
	"NodeKind",
	"LaneType",
	"ValueClass",
]
