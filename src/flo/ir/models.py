"""Minimal canonical IR models used across the FLO toolchain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import json


@dataclass
class Node:
    """A single node in the canonical IR."""

    id: str
    type: str
    attrs: Dict[str, Any] | None = None


@dataclass
class IR:
    """A minimal canonical IR data structure used by render/analysis.

    This is intentionally tiny and will be expanded as the project
    progresses. Kept as dataclasses to avoid extra runtime deps.
    """

    name: str
    nodes: List[Node]

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict representation of the IR suitable for JSON."""
        return {"name": self.name, "nodes": [self._node_to_dict(n) for n in self.nodes]}

    @staticmethod
    def _node_to_dict(n: Node) -> Dict[str, Any]:
        return {"id": n.id, "type": n.type, "attrs": (n.attrs or {})}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IR":
        """Construct an `IR` instance from a plain mapping (e.g. loaded JSON)."""
        nodes = []
        for nd in data.get("nodes", []):
            nodes.append(Node(id=nd.get("id", ""), type=nd.get("type", ""), attrs=nd.get("attrs", {})))
        return cls(name=data.get("name", ""), nodes=nodes)

    def to_json(self, path: Path | str | None = None) -> str:
        """Return a pretty-printed JSON string for the IR; optionally write to `path`."""
        d = self.to_dict()
        s = json.dumps(d, indent=2)
        if path:
            Path(path).write_text(s, encoding="utf-8")
        return s
        if path:
            Path(path).write_text(s, encoding="utf-8")
        return s

