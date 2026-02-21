from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

@dataclass
class OwnerRef:
    id: str
    name: Optional[str] = None


@dataclass
class Lane:
    id: str
    name: str
    type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    id: str
    kind: str
    name: Optional[str] = None
    lane: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    source: str
    target: str
    outcome: Optional[str] = None
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowProcess:
    process: Dict[str, Any]
    nodes: List[Node]
    edges: List[Edge]
    lanes: List[Lane] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "process": self.process,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "lanes": [asdict(l) for l in self.lanes],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FlowProcess":
        nodes = [Node(**n) for n in d.get("nodes", [])]
        edges = [Edge(**e) for e in d.get("edges", [])]
        lanes = [Lane(**l) for l in d.get("lanes", [])]
        return cls(process=d.get("process", {}), nodes=nodes, edges=edges, lanes=lanes)
