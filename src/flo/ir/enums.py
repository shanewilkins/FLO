"""IR enums for node kinds, lane types and value classes."""
from __future__ import annotations

from enum import Enum


class NodeKind(str, Enum):
    """Kinds of nodes represented in the IR."""
    
    TASK = "task"
    DECISION = "decision"
    START = "start"
    END = "end"



class LaneType(str, Enum):
    """Types of lanes used for swimlane rendering."""
    
    SWIMLANE = "swimlane"
    POOL = "pool"



class ValueClass(str, Enum):
    """Basic value classes for typed metadata."""
    
    STRING = "string"
    NUMBER = "number"
    TIMESTAMP = "timestamp"
