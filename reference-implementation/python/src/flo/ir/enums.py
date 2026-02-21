from enum import Enum


class NodeKind(str, Enum):
    START = "start"
    TASK = "task"
    DECISION = "decision"
    END = "end"
    SUBPROCESS = "subprocess"


class LaneType(str, Enum):
    ROLE = "role"
    TEAM = "team"
    SYSTEM = "system"


class ValueClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    UNKNOWN = "unknown"
