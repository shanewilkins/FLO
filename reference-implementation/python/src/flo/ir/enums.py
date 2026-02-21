"""Enumerations used by the IR models.

Keep these simple and stable; they are referenced by both the
internal and packaged modules.
"""

from enum import Enum


class NodeKind(str, Enum):
    """Kinds of nodes used in the IR."""
    
    START = "start"
    TASK = "task"
    DECISION = "decision"
    END = "end"
    SUBPROCESS = "subprocess"
    

class LaneType(str, Enum):
    """Types of lanes (role/team/system)."""

    ROLE = "role"
    TEAM = "team"
    SYSTEM = "system"


class ValueClass(str, Enum):
    """A small example value classification used in examples/tests."""

    A = "A"
    B = "B"
    C = "C"
    UNKNOWN = "unknown"
