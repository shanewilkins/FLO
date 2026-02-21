"""Public reference IR dataclass models for FLO.

These mirror the internal `src/flo` models but are packaged for
distribution as `flo_reference`.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

@dataclass
class OwnerRef:
    """Reference to an owner (author/actor) of an element."""

    id: str
    name: Optional[str] = None


@dataclass
class Lane:
    """A container representing a lane (role/team/system)."""

    id: str
    name: str
    type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """A node in the flow (task, decision, start, end)."""

    id: str
    kind: str
    name: Optional[str] = None
    lane: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """An edge between nodes, optionally labelled with an outcome."""

    source: str
    target: str
    outcome: Optional[str] = None
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowProcess:
    """A container for the whole flow process (nodes, edges, lanes)."""

    process: Dict[str, Any]
    nodes: List[Node]
    edges: List[Edge]
    lanes: List[Lane] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the flow process to a plain dict."""
        return {
            "process": self.process,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "lanes": [asdict(lane) for lane in self.lanes],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FlowProcess":
        """Deserialize a dict into a `FlowProcess` instance."""
        nodes = [Node(**n) for n in d.get("nodes", [])]
        edges = [Edge(**e) for e in d.get("edges", [])]
        lanes = [Lane(**lane) for lane in d.get("lanes", [])]
        return cls(process=d.get("process", {}), nodes=nodes, edges=edges, lanes=lanes)
