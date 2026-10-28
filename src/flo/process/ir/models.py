"""Canonical process intermediate-representation models."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

type CanonicalCollection = list[Any]


@dataclass
class Node:
    """A node in the FLO IR."""

    id: str
    type: str
    attrs: Any = None
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
        self.id = str(self.id)
        self.type = str(self.type)
        normalized_attrs = _normalize_object_mapping(self.attrs, default={}) or {}
        self.attrs = normalized_attrs
        legacy_parent = normalized_attrs.pop("subprocess_parent", None)
        parent = self.subprocess_parent
        if parent is None:
            parent = legacy_parent
        self.subprocess_parent = _normalize_optional_text(parent)
        self.name = _normalize_optional_text(self.name)
        self.description = _normalize_optional_text(self.description)
        self.lane = _normalize_optional_text(self.lane)
        self.location = _normalize_optional_text(self.location)
        # Invalid supplied shapes must reach validate_ir rather than become
        # omitted measurements or empty relations. Copy even malformed values.
        for key in (
            "consumes",
            "produces",
            "performed_by",
            "uses",
            "cycle_time",
            "wait_time",
            "changeover_time",
        ):
            setattr(self, key, deepcopy(getattr(self, key)))
        self.extensions = _normalize_object_mapping(self.extensions, default=None)


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
        self.source = str(self.source)
        self.target = str(self.target)
        self.handoff = deepcopy(self.handoff)
        self.rework = deepcopy(self.rework)
        self.extensions = _normalize_object_mapping(self.extensions, default=None)


@dataclass(init=False)
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
    lead_time: dict[str, Any] | None = None
    extensions: dict[str, Any] | None = None

    def __init__(
        self,
        name: str,
        nodes: Sequence[Any],
        edges: Sequence[Any] | None = None,
        *,
        process_metadata: Any = None,
        process_version: int | str | None = None,
        process_owner: dict[str, Any] | None = None,
        business_units: Sequence[dict[str, Any]] | None = None,
        lanes: Sequence[dict[str, Any]] | None = None,
        items: CanonicalCollection | None = None,
        resources: CanonicalCollection | None = None,
        locations: CanonicalCollection | None = None,
        render_intent: dict[str, Any] | None = None,
        lead_time: dict[str, Any] | None = None,
        extensions: dict[str, Any] | None = None,
    ) -> None:
        """Normalize all constructor inputs to the canonical node/edge model."""
        self.name = str(name)
        self.nodes = [_coerce_node(value) for value in nodes]
        self.edges = [_coerce_edge(value) for value in (edges or [])]
        self.process_metadata = _normalize_object_mapping(
            process_metadata, default=None
        )
        self.process_version = process_version
        self.process_owner = _normalize_object_mapping(process_owner, default=None)
        self.business_units = _normalize_object_list(list(business_units or []))
        self.lanes = _normalize_object_list(list(lanes or []))
        self.items = items
        self.resources = resources
        self.locations = locations
        self.render_intent = render_intent
        self.lead_time = deepcopy(lead_time)
        self.extensions = _normalize_object_mapping(extensions, default=None)
        self.__post_init__()

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
            name=value.get("name"),
            description=value.get("description"),
            lane=value.get("lane"),
            location=value.get("location"),
            consumes=value.get("consumes", []),
            produces=value.get("produces", []),
            performed_by=value.get("performed_by", []),
            uses=value.get("uses", []),
            value_class=value.get("value_class"),
            cycle_time=value.get("cycle_time"),
            wait_time=value.get("wait_time"),
            changeover_time=value.get("changeover_time"),
            extensions=value.get("extensions"),
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
            route=value.get("route"),
            label=value.get("label"),
            handoff=value.get("handoff"),
            rework=value.get("rework"),
            extensions=value.get("extensions"),
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
