"""Canonical process intermediate-representation models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from typing import Any

type CanonicalCollection = list[dict[str, Any]] | dict[str, Any]


@dataclass
class Node:
    """A node in the FLO IR."""

    id: str
    type: str
    branch: dict[str, Any] | None = None
    subprocess_parent: str | None = None
    name: str | None = None
    description: str | None = None
    lane: str | None = None
    location: str | None = None
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    performed_by: list[str] = field(default_factory=list)
    uses: list[str] = field(default_factory=list)
    value_class: str | None = None
    cycle_time: dict[str, Any] | None = None
    wait_time: dict[str, Any] | None = None
    changeover_time: dict[str, Any] | None = None
    extensions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Detach supplied semantics without concealing malformed values."""
        for entry in fields(self):
            setattr(self, entry.name, deepcopy(getattr(self, entry.name)))


@dataclass
class Edge:
    """A directed edge in the FLO IR."""

    source: str
    target: str
    id: str | None = None
    outcome: str | None = None
    route: str | None = None
    label: str | None = None
    handoff: dict[str, Any] | None = None
    rework: dict[str, Any] | None = None
    extensions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Detach relation data while retaining invalid shapes for validation."""
        for entry in fields(self):
            setattr(self, entry.name, deepcopy(getattr(self, entry.name)))


@dataclass
class IR:
    """Represents a FLO intermediate representation (IR)."""

    name: str
    nodes: list[Node]
    edges: list[Edge] = field(default_factory=list)
    process_metadata: dict[str, Any] | None = None
    process_version: int | str | None = None
    process_owner: dict[str, Any] | None = None
    business_units: list[dict[str, Any]] = field(default_factory=list)
    lanes: list[dict[str, Any]] | None = None
    items: CanonicalCollection | None = None
    resources: CanonicalCollection | None = None
    locations: CanonicalCollection | None = None
    render_intent: dict[str, Any] | None = None
    lead_time: dict[str, Any] | None = None
    extensions: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Detach context without coercing shapes or promoting metadata."""
        if any(not isinstance(node, Node) for node in self.nodes):
            raise TypeError("IR.nodes entries must be Node instances")
        if any(not isinstance(edge, Edge) for edge in self.edges):
            raise TypeError("IR.edges entries must be Edge instances")
        self.nodes = list(self.nodes)
        self.edges = list(self.edges)
        for entry in fields(self):
            if entry.name not in {"nodes", "edges"}:
                setattr(self, entry.name, deepcopy(getattr(self, entry.name)))
