"""Canonical IR models moved under compiler.ir."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """A node in the FLO IR."""

    id: str
    type: str
    attrs: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Normalize scalar and mapping fields after dataclass initialization."""
        self.id = str(self.id)
        self.type = str(self.type)
        self.attrs = _normalize_object_mapping(self.attrs, default={})


@dataclass
class Edge:
    """A directed edge in the FLO IR."""

    source: str
    target: str
    id: str | None = None
    outcome: str | None = None
    label: str | None = None
    edge_type: str | None = None
    handoff: bool | None = None
    rework: bool | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Normalize endpoint identifiers and optional metadata mapping."""
        self.source = str(self.source)
        self.target = str(self.target)
        self.metadata = _normalize_object_mapping(self.metadata, default=None)


@dataclass
class IR:
    """Represents a FLO intermediate representation (IR)."""

    name: str
    nodes: list[Node]
    edges: list[Edge] = field(default_factory=list)
    process_metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Coerce nested node/edge entries and normalize optional metadata."""
        self.name = str(self.name)
        self.nodes = [_coerce_node(value) for value in self.nodes]
        self.edges = [_coerce_edge(value) for value in self.edges]
        self.process_metadata = _normalize_object_mapping(
            self.process_metadata,
            default=None,
        )


def _coerce_node(value: Any) -> Node:
    if isinstance(value, Node):
        return value
    if isinstance(value, dict):
        return Node(
            id=value.get("id", ""),
            type=value.get("type", ""),
            attrs=value.get("attrs", {}),
        )
    raise TypeError(f"IR.nodes entries must be Node or dict, got {type(value)!r}")


def _coerce_edge(value: Any) -> Edge:
    if isinstance(value, Edge):
        return value
    if isinstance(value, dict):
        return Edge(
            source=value.get("source", ""),
            target=value.get("target", ""),
            id=value.get("id"),
            outcome=value.get("outcome"),
            label=value.get("label"),
            edge_type=value.get("edge_type"),
            handoff=value.get("handoff"),
            rework=value.get("rework"),
            metadata=value.get("metadata"),
        )
    raise TypeError(f"IR.edges entries must be Edge or dict, got {type(value)!r}")


def _normalize_object_mapping(
    value: object,
    *,
    default: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return default
