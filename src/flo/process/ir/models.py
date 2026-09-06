"""Canonical process intermediate-representation models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

type CanonicalCollection = list[Any] | dict[str, Any]


@dataclass
class Node:
    """A node in the FLO IR."""

    id: str
    type: str
    attrs: dict[str, Any] | None = None
    subprocess_parent: str | None = None

    def __post_init__(self) -> None:
        """Normalize scalar and mapping fields after dataclass initialization."""
        self.id = str(self.id)
        self.type = str(self.type)
        normalized_attrs = _normalize_object_mapping(self.attrs, default={}) or {}
        self.attrs = normalized_attrs
        legacy_parent = normalized_attrs.pop("subprocess_parent", None)
        parent = self.subprocess_parent
        if parent is None:
            parent = legacy_parent
        self.subprocess_parent = _normalize_optional_text(parent)


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
    process_version: int | str | None = None
    process_owner: dict[str, Any] | None = None
    business_units: list[dict[str, Any]] = field(default_factory=list)
    lanes: list[dict[str, Any]] = field(default_factory=list)
    items: CanonicalCollection | None = None
    resources: CanonicalCollection | None = None
    locations: CanonicalCollection | None = None
    render_intent: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Coerce nested node/edge entries and normalize optional metadata."""
        self.name = str(self.name)
        if not isinstance(self.process_version, (int, str)) or isinstance(
            self.process_version, bool
        ):
            self.process_version = None
        self.nodes = [_coerce_node(value) for value in self.nodes]
        self.edges = [_coerce_edge(value) for value in self.edges]
        self.process_metadata = _normalize_object_mapping(
            self.process_metadata,
            default=None,
        )
        metadata = self.process_metadata or {}
        self.items = _promote_metadata_value(metadata, "items", self.items)
        self.resources = _promote_metadata_value(metadata, "resources", self.resources)
        self.locations = _promote_metadata_value(metadata, "locations", self.locations)
        self.render_intent = _promote_metadata_value(
            metadata, "render", self.render_intent
        )
        self.process_metadata = metadata or None
        self.process_owner = _normalize_object_mapping(self.process_owner, default=None)
        self.business_units = _normalize_object_list(self.business_units)
        self.lanes = _normalize_object_list(self.lanes)


def _coerce_node(value: Any) -> Node:
    if isinstance(value, Node):
        return value
    if isinstance(value, dict):
        return Node(
            id=value.get("id", ""),
            type=value.get("type", ""),
            attrs=value.get("attrs", {}),
            subprocess_parent=value.get("subprocess_parent"),
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
        return deepcopy(value)
    return default


def _normalize_object_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(entry) for entry in value if isinstance(entry, dict)]


def _promote_metadata_value(
    metadata: dict[str, Any], key: str, explicit_value: Any
) -> Any:
    legacy_value = metadata.pop(key, None)
    return deepcopy(explicit_value if explicit_value is not None else legacy_value)


def _normalize_optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
