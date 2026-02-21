# FLO Ontology — v0.0 draft

Purpose
-------

This document defines the core domain concepts FLO uses to represent organizational
processes. The goal is a small, well-scoped vocabulary that maps directly to the
FLO IR and the YAML surface.

Core concepts
-------------

- Process: A named model describing a sequence of work for achieving an outcome.
	- id (string), name (string), version (number/string), owner (ref)
	- metadata: freeform key/value annotations (e.g., `value_class`, `sla_target_seconds`)

- Step (Node): A discrete element in a process graph. Kinds include `start`,
	`task`, `decision`, `end`, and `subprocess` (future).
	- id (string), kind (enum), name (string), lane (ref), annotations

- Transition (Edge): A directed connection between two `Step`s.
	- source (step id), target (step id), condition/outcome (optional), label (optional)

- Lane: A partitioning construct representing organizational ownership or
	responsibility (role, team, system). Lanes are used for swimlane projections.
	- id, name, type (role|team|system)

- Outcome / Condition: Named label on an outgoing `Transition` (e.g., `yes`, `no`).

- Business Unit / Organization: High-level grouping of lanes and owners.

- Artifact: A document, data object, or input/output produced or consumed by a Step.

- Event (runtime / telemetry): An observation emitted during real executions.
	- canonical fields: `case_id`, `activity_key`, `timestamp`, `actor`, `metadata`

- Case (instance): A single execution instance of a `Process` (identified by `case_id`).

Representation: canonical FLO IR (conceptual)
------------------------------------------------

At the IR level a `Process` is a pair: `({nodes}, {edges})` where:

- `nodes` is a list of node objects `{ id, kind, name, lane?, metadata? }`.
- `edges` is a list of edge objects `{ id?, source, target, outcome?, metadata? }`.

This minimal representation maps directly to YAML and to projections (DOT, graphs).

DAG vs cycles — modelling choices and recommendations
-----------------------------------------------------

- Idealized view: A process as a Directed Acyclic Graph (DAG) simplifies many
	static analyses (topological ordering, deterministic longest-path). Some
	projections and UI flows benefit from an acyclic representation.

- Reality: Real business processes commonly contain cycles (rework loops,
	iterative approvals, retries). FLO must model these explicitly rather than
	ban them.

- FLO approach:
	- The canonical IR is a directed graph (not restricted to acyclic).
	- Algorithms that require acyclicity operate on the SCC-condensed graph
		(strongly connected components collapsed to macro-nodes). This produces a
		DAG and preserves linear-time bounds for traversal: SCC computation is O(N+E).
	- Rework loops are detectable by identifying edges that point back into an
		ancestor SCC. These are reported as explicit `rework` findings by static
		analysis.

- Analysis implications:
	- Longest simple-path in a general graph is hard; for analysis we use one of:
		- compute longest path on SCC-DAG using node/edge weights aggregated per SCC, or
		- compute critical path over an acyclic unfolding (bounded unrolling) for
			small, intentionally modeled loops.
	- Handoff counts, loop detection, and visit-frequency summaries are linear
		in the size of the graph once SCCs are computed.

Design guardrails
-----------------

- No implicit looping constructs with unbounded counters or embedded scripts.
	Loops must be explicit via edges and decision nodes.
- Keep node/edge metadata small and typed (string, number, enum) to facilitate
	validation and projections.
- Every feature must justify itself in one paragraph and map deterministically
	to the IR.

Metrics & annotations (examples)
--------------------------------

- `sla_target_seconds` (node metadata): expected service time for that step.
- `value_class` (process or node): impact classification for Lean analysis.
- `handoff` (edge metadata): boolean/enum to indicate cross-lane handoffs.

Telemetry mapping notes
-----------------------

- Minimal event schema to align with v0.3 roadmap: `{ case_id, activity_key, timestamp }`.
- The `activity_key` should map to `node.id` (or a stable canonical key) so
	that traces can be aligned to the IR deterministically.

Next steps
----------

- Iterate on this draft with concrete YAML examples and counterexamples.
- Draft the initial FLO IR spec (JSON Schema + examples) that implements the
	`({nodes},{edges})` model and SCC/DAG conventions.
- Add a small conformance example set in `examples/` to validate parsing and
	SCC-based analyses (e.g., simple linear process, process with a rework loop).

---

Document version: draft (v0.0)
