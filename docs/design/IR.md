Canonical FLO Process Model (CPM) – v0.1

Purpose: Provide a stable intermediate representation (IR) for FLO that
separates the DSL surface syntax from analysis, visualization, and
downstream tooling.

Design goals: - Canonical - Graph-native - Typed -
Serialization-friendly - Stable for downstream packages (e.g., lss4py)

------------------------------------------------------------------------

PROCESS

Process - id: str - name: str | None - version: str | None -
description: str | None - metadata: dict[str, Any] - nodes: dict[str,
Node] - edges: list[Edge] - lanes: dict[str, Lane] | None - artifacts:
dict[str, Artifact] | None

Rules: - id must be unique and stable. - metadata stores non-semantic
annotations.

------------------------------------------------------------------------

NODE

Node - id: str - type: NodeType - name: str | None - lane: str | None -
io: IO | None - timing: Timing | None - guard: str | None - metadata:
dict[str, Any]

NodeType (MVP set) - start - end - task - system_task - decision - merge
(optional) - fork (later) - join (later)

------------------------------------------------------------------------

EDGE

Edge - id: str | None - source: str - target: str - type: EdgeType -
condition: str | None - probability: float | None - metadata: dict[str,
Any]

EdgeType - sequence - message (future)

------------------------------------------------------------------------

LANE

Lane - id: str - name: str | None - kind: LaneKind - metadata: dict[str,
Any]

LaneKind - human - system - org_unit - external

------------------------------------------------------------------------

IO

IO - inputs: list[ItemRef] - outputs: list[ItemRef]

ItemRef - id: str | None - name: str - kind: str | None - metadata:
dict[str, Any]

------------------------------------------------------------------------

TIMING

Timing - expected_duration_s: int | None - sla_s: int | None -
wait_time_s: int | None

------------------------------------------------------------------------

CANONICALIZATION RULES

Identity - Every node must have a unique id. - Exactly one start node. -
At least one end node is required.

Edge validity - All referenced nodes must exist.

Decision semantics - decision nodes must have at least two outgoing
edges. - edges may contain conditions. - one edge may be default
(condition null or “else”).

Graph validation - reachability from start recommended - orphan nodes
errors - every non-start node must have at least one predecessor - every
non-end node must have at least one successor - every node must be reachable
from start - every node must be able to reach at least one end node - cycles
allowed but reported

Validation diagnostics (current)

- E1003: exactly one start node required
- E1004: unresolved edge endpoint
- E1005: decision must have at least two outgoing edges
- E1006: non-start node missing predecessor
- E1007: non-end node missing successor
- E1008: node unreachable from start
- E1009: node cannot reach any end node
- E1010: at least one end node required

------------------------------------------------------------------------

SERIALIZATION PRINCIPLE

JSON is a serialization of CPM, not the IR itself. Primary IR lives as
typed objects in code (dataclasses / pydantic).

------------------------------------------------------------------------

MVP SCOPE

Required: - Process - Node types: start, end, task, system_task,
decision - Edge with optional condition - Optional lanes - Validation -
DOT export

Deferred: - parallel gateways - simulation parameters - statistical
analysis - mining algorithms

------------------------------------------------------------------------

BOUNDARY WITH LSS4PY

FLO describes process structure. lss4py analyzes operational behavior.

Data flow:

FLO YAML -> FLO parser -> Canonical Process Model (CPM) -> handed to
lss4py for metrics / mining / statistics