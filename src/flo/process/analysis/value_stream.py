"""Backend-neutral value-stream projection over canonical FLO IR."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from flo.process.ir.metadata import extract_node_metadata
from flo.process.ir.models import IR, Node

from .process_metadata import extract_process_metadata
from .timing import analyze_process_timing

FlowKind = Literal["information", "material"]
_VISIBLE_NODE_TYPES = frozenset(
    {"task", "system_task", "subprocess", "queue", "decision"}
)


@dataclass(frozen=True)
class ValueStreamNode:
    """One process-anchored node and its declared lean timing metrics."""

    node_id: str
    name: str
    node_type: str
    cycle_time_seconds: float | None = None
    wait_time_seconds: float | None = None
    changeover_time_seconds: float | None = None


@dataclass(frozen=True)
class ValueStreamFlow:
    """One declared item flow between process nodes or an external boundary."""

    kind: FlowKind
    item_id: str
    item_name: str
    source_node_id: str | None
    target_node_id: str | None


@dataclass(frozen=True)
class ValueStreamDiagnostic:
    """A deterministic limitation disclosed by the value-stream projection."""

    code: str
    message: str


@dataclass(frozen=True)
class ValueStreamProjection:
    """Stable renderer-neutral value-stream surface."""

    projection_version: str
    process_id: str
    process_name: str
    nodes: tuple[ValueStreamNode, ...]
    information_flows: tuple[ValueStreamFlow, ...]
    material_flows: tuple[ValueStreamFlow, ...]
    diagnostics: tuple[ValueStreamDiagnostic, ...]
    modeled_lead_time_seconds: float | None

    @property
    def partial(self) -> bool:
        """Return whether either required flow surface is absent."""
        return not self.information_flows or not self.material_flows

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""
        return {
            "projection_version": self.projection_version,
            "process": {"id": self.process_id, "name": self.process_name},
            "partial": self.partial,
            "modeled_lead_time_seconds": self.modeled_lead_time_seconds,
            "nodes": [asdict(node) for node in self.nodes],
            "information_flows": [asdict(flow) for flow in self.information_flows],
            "material_flows": [asdict(flow) for flow in self.material_flows],
            "diagnostics": [asdict(diagnostic) for diagnostic in self.diagnostics],
        }


def project_value_stream(process: IR) -> ValueStreamProjection:
    """Project canonical process, item, and timing facts for VSM rendering."""
    if not isinstance(process, IR):
        raise TypeError("project_value_stream requires canonical IR")

    timing = analyze_process_timing(process)
    timing_by_node = {entry.node_id: entry for entry in timing.node_timings}
    visible_nodes = tuple(
        _project_node(node, timing_by_node=timing_by_node)
        for node in process.nodes
        if node.type in _VISIBLE_NODE_TYPES
    )
    visible_ids = frozenset(node.node_id for node in visible_nodes)
    information, material = _project_item_flows(process, visible_ids=visible_ids)
    diagnostics = _flow_diagnostics(information=information, material=material)
    metadata = extract_process_metadata(process)
    return ValueStreamProjection(
        projection_version="0.1",
        process_id=str(metadata.get("process_id") or process.name),
        process_name=str(metadata.get("process_name") or process.name),
        nodes=visible_nodes,
        information_flows=information,
        material_flows=material,
        diagnostics=diagnostics,
        modeled_lead_time_seconds=timing.modeled_lead_time_seconds,
    )


def _project_node(node: Node, *, timing_by_node: dict[str, Any]) -> ValueStreamNode:
    metadata = extract_node_metadata(node)
    timing = timing_by_node[node.id]
    return ValueStreamNode(
        node_id=node.id,
        name=str((node.attrs or {}).get("name") or node.id),
        node_type=node.type,
        cycle_time_seconds=(
            timing.totals.cycle_time_seconds if "cycle_time" in metadata else None
        ),
        wait_time_seconds=(
            timing.totals.wait_time_seconds if "wait_time" in metadata else None
        ),
        changeover_time_seconds=(
            timing.totals.changeover_time_seconds
            if timing.changeover_source_field is not None
            else None
        ),
    )


def _project_item_flows(
    process: IR, *, visible_ids: frozenset[str]
) -> tuple[tuple[ValueStreamFlow, ...], tuple[ValueStreamFlow, ...]]:
    node_relations = _node_item_relations(process, visible_ids=visible_ids)
    node_order = {node_id: index for index, node_id in enumerate(node_relations)}
    adjacency = _adjacency(process)
    by_kind: dict[FlowKind, list[ValueStreamFlow]] = {
        "information": [],
        "material": [],
    }
    for item in _item_entries(process.items):
        kind = _flow_kind(item)
        if kind is None:
            continue
        by_kind[kind].extend(
            _project_item(
                item,
                kind=kind,
                node_relations=node_relations,
                node_order=node_order,
                adjacency=adjacency,
            )
        )
    return tuple(sorted(by_kind["information"], key=_flow_sort_key)), tuple(
        sorted(by_kind["material"], key=_flow_sort_key)
    )


def _node_item_relations(
    process: IR, *, visible_ids: frozenset[str]
) -> dict[str, tuple[frozenset[str], frozenset[str]]]:
    return {
        node.id: (
            _text_values((node.attrs or {}).get("consumes")),
            _text_values((node.attrs or {}).get("produces")),
        )
        for node in process.nodes
        if node.id in visible_ids
    }


def _flow_kind(item: dict[str, Any]) -> FlowKind | None:
    kind = str(item.get("kind") or "").strip().lower()
    if kind == "information":
        return "information"
    if kind == "material":
        return "material"
    return None


def _project_item(
    item: dict[str, Any],
    *,
    kind: FlowKind,
    node_relations: dict[str, tuple[frozenset[str], frozenset[str]]],
    node_order: dict[str, int],
    adjacency: dict[str, tuple[str, ...]],
) -> list[ValueStreamFlow]:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        return []
    producers = _nodes_declaring_item(node_relations, item_id=item_id, relation=1)
    consumers = _nodes_declaring_item(node_relations, item_id=item_id, relation=0)
    return _connect_item(
        kind=kind,
        item_id=item_id,
        item_name=str(item.get("name") or item_id),
        producers=producers,
        consumers=consumers,
        node_order=node_order,
        adjacency=adjacency,
    )


def _nodes_declaring_item(
    node_relations: dict[str, tuple[frozenset[str], frozenset[str]]],
    *,
    item_id: str,
    relation: int,
) -> list[str]:
    return [
        node_id
        for node_id, relations in node_relations.items()
        if item_id in relations[relation]
    ]


def _flow_sort_key(flow: ValueStreamFlow) -> tuple[str, str, str]:
    return (
        flow.item_id,
        flow.source_node_id or "",
        flow.target_node_id or "~",
    )


def _connect_item(
    *,
    kind: str,
    item_id: str,
    item_name: str,
    producers: list[str],
    consumers: list[str],
    node_order: dict[str, int],
    adjacency: dict[str, tuple[str, ...]],
) -> list[ValueStreamFlow]:
    flow_kind: FlowKind = "information" if kind == "information" else "material"
    pairs: list[tuple[str | None, str | None]] = []
    for target in consumers:
        upstream = [
            source
            for source in producers
            if source != target
            and _reachable_distance(source, target, adjacency=adjacency) is not None
        ]
        source = (
            min(
                upstream,
                key=lambda candidate: (
                    _reachable_distance(candidate, target, adjacency=adjacency) or 0,
                    node_order[candidate],
                ),
            )
            if upstream
            else None
        )
        pairs.append((source, target))
    for source in producers:
        if not any(
            target != source
            and _reachable_distance(source, target, adjacency=adjacency) is not None
            for target in consumers
        ):
            pairs.append((source, None))
    return [
        ValueStreamFlow(flow_kind, item_id, item_name, source, target)
        for source, target in pairs
    ]


def _flow_diagnostics(
    *, information: tuple[ValueStreamFlow, ...], material: tuple[ValueStreamFlow, ...]
) -> tuple[ValueStreamDiagnostic, ...]:
    diagnostics: list[ValueStreamDiagnostic] = []
    if not information:
        diagnostics.append(
            ValueStreamDiagnostic(
                "value-stream-information-absent",
                "No declared information-item flow is available.",
            )
        )
    if not material:
        diagnostics.append(
            ValueStreamDiagnostic(
                "value-stream-material-absent",
                "No declared material-item flow is available.",
            )
        )
    return tuple(diagnostics)


def _item_entries(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, dict))
    if isinstance(value, dict):
        return tuple(
            {"id": item_id, **item}
            for item_id, item in value.items()
            if isinstance(item, dict)
        )
    return ()


def _text_values(value: Any) -> frozenset[str]:
    if not isinstance(value, list):
        return frozenset()
    return frozenset(str(item) for item in value if str(item).strip())


def _adjacency(process: IR) -> dict[str, tuple[str, ...]]:
    targets: dict[str, list[str]] = {node.id: [] for node in process.nodes}
    for edge in process.edges:
        targets.setdefault(edge.source, []).append(edge.target)
    return {source: tuple(sorted(values)) for source, values in targets.items()}


def _reachable_distance(
    source: str, target: str, *, adjacency: dict[str, tuple[str, ...]]
) -> int | None:
    frontier = [(source, 0)]
    visited = {source}
    while frontier:
        current, distance = frontier.pop(0)
        for neighbor in adjacency.get(current, ()):
            if neighbor == target:
                return distance + 1
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, distance + 1))
    return None
