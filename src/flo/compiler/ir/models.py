"""Canonical IR models moved under compiler.ir."""

from __future__ import annotations

from dataclasses import dataclass
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
class IR:
    """Represents a FLO intermediate representation (IR)."""

    name: str
    nodes: List[Node]
    schema_aligned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation of the IR.

        If `schema_aligned` is False this returns a lightweight dict;
        otherwise it returns the schema-shaped representation.
        """
        if not self.schema_aligned:
            return {"name": self.name, "nodes": [self._node_to_dict(n) for n in self.nodes]}
        return self._to_schema_dict()

    def _to_schema_dict(self) -> Dict[str, Any]:
        proc_id = self.name or "generated"
        process = {"id": proc_id, "name": proc_id}

        nodes_out: List[Dict[str, Any]] = []
        edge_pairs: List[tuple[str, str]] = []

        for n in self.nodes:
            nd: Dict[str, Any] = {"id": n.id, "kind": n.type}
            attrs = n.attrs or {}
            if isinstance(attrs, dict):
                name = attrs.get("name")
                if name is not None:
                    nd["name"] = name
                lane = attrs.get("lane")
                if lane is not None:
                    nd["lane"] = lane
                targets = attrs.get("edges") or []
                if isinstance(targets, list):
                    for tgt in targets:
                        edge_pairs.append((n.id, str(tgt)))

            nodes_out.append(nd)

        edges_out: List[Dict[str, Any]] = [
            {"id": f"e_{i}", "source": s, "target": t} for i, (s, t) in enumerate(edge_pairs)
        ]

        return {"process": process, "nodes": nodes_out, "edges": edges_out}

    @staticmethod
    def _node_to_dict(n: Node) -> Dict[str, Any]:
        """Convert a `Node` instance to a plain dict."""
        return {"id": n.id, "type": n.type, "attrs": (n.attrs or {})}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IR":
        """Construct an `IR` from a dict representation."""
        nodes = []
        for nd in data.get("nodes", []):
            nodes.append(Node(id=nd.get("id", ""), type=nd.get("type", ""), attrs=nd.get("attrs", {})))
        return cls(name=data.get("name", ""), nodes=nodes)

    def to_json(self, path: Path | str | None = None) -> str:
        """Serialize the IR to JSON and optionally write to `path`."""
        d = self.to_dict()
        s = json.dumps(d, indent=2)
        if path:
            Path(path).write_text(s, encoding="utf-8")
        return s
