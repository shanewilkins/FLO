# FLO IR — initial draft (v0.0)

Purpose
-------

This document defines the canonical Intermediate Representation (IR) for FLO.
The IR is intentionally small and maps deterministically from the YAML surface
to a simple graph form suitable for projections, validation, and static analysis.

Overview
--------

At a conceptual level a `Process` in the FLO IR is an object with two top-level
collections: `nodes` and `edges`.

- `nodes`: an array of node objects; each node is a Step in the process graph.
- `edges`: an array of directed edges (transitions) between nodes.

The IR is a directed graph (not restricted to acyclic). Tools that require
acyclicity operate on the SCC-condensed DAG.

Top-level JSON-like model (concept)
-----------------------------------

{
  "process": { "id": "...", "name": "...", "version": "...", "metadata": {...} },
  "nodes": [ { node }, ... ],
  "edges": [ { edge }, ... ]
}

Node object
-----------

- `id` (string, required): stable identifier for the node.
- `kind` (enum: `start` | `task` | `decision` | `end` | `subprocess`) required.
- `name` (string): human-facing label.
- `lane` (string, optional): `lane.id` this node belongs to.
- `metadata` (object, optional): typed key/value annotations (string|number|enum).

Edge object
-----------

- `id` (string, optional): stable identifier for the edge.
- `source` (string, required): `node.id` of origin.
- `target` (string, required): `node.id` of destination.
- `outcome` (string, optional): outcome label (e.g., `yes`, `no`).
- `label` (string, optional): human label.
- `metadata` (object, optional): typed annotations (e.g., `handoff`: boolean).

Lane object (concept)
---------------------

- `id` (string), `name` (string), `type` (role|team|system), `metadata` (opt)

Validation rules (initial)
--------------------------

- All `source` and `target` references in `edges` must resolve to a `node.id`.
- Exactly one `start` node is recommended; multiple start nodes allowed but
  must be intentional and validated by policy.
- `decision` nodes should have outgoing edges with `outcome` labels; missing
  outcome labels produce a diagnostic.
- No implicit node creation; all nodes and lanes must be declared.

JSON Schema (sketch)
--------------------

This is a compact, conceptual JSON Schema to capture the IR shape. A formal
schema file (`schema/flo_ir.json`) should be derived from this sketch.

{
  "type": "object",
  "required": ["process","nodes","edges"],
  "properties": {
    "process": { "type": "object" },
    "nodes": { "type": "array" },
    "edges": { "type": "array" }
  }
}

Examples
--------

YAML surface (simple linear process):

```yaml
spec_version: "0.1"
process:
  id: onboarding_v1
  name: Client Onboarding
  version: 1
  owner:
    id: ops_mgr
    name: Ops Manager
lanes:
  - id: sales
    name: Sales
  - id: ops
    name: Operations
steps:
  - id: start
    kind: start
    name: Start
  - id: collect_docs
    kind: task
    name: Collect Documents
    lane: sales
  - id: verify
    kind: task
    name: Verify Documents
    lane: ops
  - id: approved
    kind: decision
    name: Approved?
    outcomes:
      yes: finish
      no: collect_docs
  - id: finish
    kind: end
    name: Complete
```

Corresponding FLO IR (conceptual):

```json
{
  "process": { "id": "onboarding_v1", "name": "Client Onboarding" },
  "nodes": [
    { "id": "start", "kind": "start", "name": "Start" },
    { "id": "collect_docs", "kind": "task", "name": "Collect Documents", "lane": "sales" },
    { "id": "verify", "kind": "task", "name": "Verify Documents", "lane": "ops" },
    { "id": "approved", "kind": "decision", "name": "Approved?" },
    { "id": "finish", "kind": "end", "name": "Complete" }
  ],
  "edges": [
    { "source": "start", "target": "collect_docs" },
    { "source": "collect_docs", "target": "verify" },
    { "source": "verify", "target": "approved" },
    { "source": "approved", "target": "finish", "outcome": "yes" },
    { "source": "approved", "target": "collect_docs", "outcome": "no" }
  ]
}
```

SCC / DAG conventions

  acyclic macro-graph for analyses that require DAGs. SCC nodes aggregate:
  - member node ids
  - aggregated metadata (e.g., sum/mean of `sla_target_seconds` where numeric)


SCC condensation (explicit explanation)
--------------------------------------

What is an SCC-condensed DAG?

- An SCC (strongly connected component) is a maximal set of nodes in a directed
  graph where each node is reachable from every other node in the set.
- Condensing the graph means collapsing each SCC into a single macro-node and
  then preserving edges between SCCs. The resulting graph is guaranteed to be
  a Directed Acyclic Graph (DAG) because SCCs capture all cycles.

Why do this?

- Many static analyses (topological ordering, DAG longest-path, incremental
  validation) require an acyclic graph. Working on the SCC-condensed DAG lets us
  reason about high-level flow while keeping the original cyclic semantics in
  the per-SCC detail.

How to compute (algorithmic sketch)

- Use any linear-time SCC algorithm (Tarjan's algorithm or Kosaraju's
  algorithm). Both run in O(N + E) time where N is number of nodes and E is
  number of edges.
- Steps:
  1. Run Tarjan/Kosaraju to partition `nodes` into SCCs.
  2. Create a macro-node for each SCC and record its member node ids.
  3. For every original edge (u -> v):
     - if SCC(u) == SCC(v) then it is an internal edge (retained in the SCC's
       internal representation), otherwise add/merge an edge from SCC(u) -> SCC(v)
       on the condensed graph.

Aggregation & metadata rules

- Member list: each macro-node stores the list of `node.id`s it contains.
- Aggregated numeric metadata: for metrics like `sla_target_seconds` the macro-node
  should store both `sum` and `mean` (or other sensible aggregations) so callers
  can choose semantics.
- Categorical metadata: collect unique values or counts (e.g., distinct
  `value_class` tags) depending on consumer needs.
- Edge metadata: when multiple original edges between two SCCs exist, the
  condensed edge should preserve a list of original edges (or an aggregated
  summary) including their `outcome` labels and any `handoff` flags.

Preserving analysis correctness

- Rework detection: an SCC with size > 1 or an SCC containing a self-loop
  indicates cyclic behavior (a rework loop). Edges from a later SCC back to an
  earlier SCC indicate cross-SCC rework; these are detectable by comparing a
  topological order on the condensed DAG.
- Longest-path: compute longest path on the SCC-DAG using aggregated node
  weights (e.g., sum of `sla_target_seconds`) — this yields a conservative
  estimate of the critical path that accounts for intra-SCC cycles by aggregation.

Complexity and performance

- SCC condensation is O(N + E) time and O(N + E) memory; it preserves the
  linear-time design goal for FLO analyses.

Example (small)

- Original graph nodes: A -> B -> C -> B (B<->C cycle), and C -> D.
- SCCs: {A}, {B,C}, {D}.
- Condensed DAG: A -> {B,C} -> D.

Usage guidance for implementers

- Provide both representations in tools: the original IR (full graph) and the
  condensed DAG (macro-nodes + condensed edges). Consumers can pick the level
  of detail they need.
- Keep mapping tables: from `node.id` to `scc_id` and from original `edge` to
  condensed edge id for traceability back to the original graph.

---
Projections and consumers
-------------------------

- DOT renderer: map `nodes` to DOT nodes and `edges` to directed edges; include
  lane grouping as subgraphs for swimlane output.
- Swimlane projection: group nodes by `lane` and render cross-lane `handoff`
  edges with an edge metadata flag.
- Validators and static-analyzers consume the IR directly.

Next steps
----------

- Produce a formal JSON Schema (`schema/flo_ir.json`) and place it in the repo.
- Add two canonical examples to `examples/`: `linear.flo` and `rework_loop.flo`.
- Implement a small IR serializer in the reference implementation (`flo.model`)
  that converts parsed YAML into this IR shape and unit-tests the mapping.

Document version: draft (v0.0)
