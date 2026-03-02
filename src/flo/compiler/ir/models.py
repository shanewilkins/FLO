"""Canonical IR models moved under compiler.ir."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path
import json


@dataclass
class Node:
    """A node in the FLO IR."""

    id: str
    type: str
    attrs: Dict[str, Any] | None = None


@dataclass
class Edge:
    """A directed edge in the FLO IR."""

    source: str
    target: str
    id: str | None = None
    outcome: str | None = None
    label: str | None = None
    metadata: Dict[str, Any] | None = None


@dataclass
class IR:
    """Represents a FLO intermediate representation (IR)."""

    name: str
    nodes: List[Node]
    edges: List[Edge] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a Python-native dict representation of the canonical IR."""
        return {
            "name": self.name,
            "nodes": [self._node_to_dict(n) for n in self.nodes],
            "edges": [self._edge_to_dict(e) for e in self.edges],
        }

    @staticmethod
    def _node_to_dict(n: Node) -> Dict[str, Any]:
        """Convert a `Node` instance to a plain dict."""
        return {"id": n.id, "type": n.type, "attrs": (n.attrs or {})}

    @staticmethod
    def _edge_to_dict(e: Edge) -> Dict[str, Any]:
        """Convert an `Edge` instance to a plain dict."""
        out: Dict[str, Any] = {"source": e.source, "target": e.target}
        if e.id is not None:
            out["id"] = e.id
        if e.outcome is not None:
            out["outcome"] = e.outcome
        if e.label is not None:
            out["label"] = e.label
        if e.metadata is not None:
            out["metadata"] = e.metadata
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IR":
        """Construct an `IR` from a dict representation."""
        nodes = []
        for nd in data.get("nodes", []):
            nodes.append(Node(id=nd.get("id", ""), type=nd.get("type", ""), attrs=nd.get("attrs", {})))
        edges = []
        for ed in data.get("edges", []):
            edges.append(
                Edge(
                    source=ed.get("source", ""),
                    target=ed.get("target", ""),
                    id=ed.get("id"),
                    outcome=ed.get("outcome"),
                    label=ed.get("label"),
                    metadata=ed.get("metadata"),
                )
            )
        return cls(name=data.get("name", ""), nodes=nodes, edges=edges)

    def to_json(self, path: Path | str | None = None) -> str:
        """Serialize the IR to JSON and optionally write to `path`."""
        d = self.to_dict()
        s = json.dumps(d, indent=2)
        if path:
            Path(path).write_text(s, encoding="utf-8")
        return s
