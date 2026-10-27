"""Enum-like constants for IR (moved under compiler.ir)."""

from enum import Enum


class NodeKind(Enum):
    """Kinds of nodes present in the IR."""

    TASK = "task"
    WAIT = "wait"
    PROCESS = "process"
    DECISION = "decision"
    BRANCH = "branch"


class LaneType(Enum):
    """Types of lanes used to group nodes."""

    SWIMLANE = "swimlane"
    GROUP = "group"


class ValueClass(Enum):
    """Semantic classes for typed values in node attributes."""

    STRING = "string"
    NUMBER = "number"


class ProcessValueClass(Enum):
    """Lean value classification for process steps."""

    VA = "VA"
    RNVA = "RNVA"
    NVA = "NVA"
    UNKNOWN = "unknown"


VALUE_CLASS_NODE_KINDS = frozenset(
    {"task", "system_task", "subprocess", "queue", "wait"}
)


__all__ = [
    "VALUE_CLASS_NODE_KINDS",
    "LaneType",
    "NodeKind",
    "ProcessValueClass",
    "ValueClass",
]
