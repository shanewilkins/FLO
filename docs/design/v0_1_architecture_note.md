# FLO v0.1 Architecture Note (Syntax, Semantics, and Boundaries)

Status: draft for v0.1 freeze

## 0) Ratified Decisions (March 2026)

The following decisions are approved and treated as baseline direction:

- End-state focus: FLO serves process improvement practitioners (Lean Six Sigma, operations analysts, consultants, industrial engineering students) with plain-text, versionable process models.
- Model split: designed process and observed process stay separate, linked by an explicit alignment/conformance layer.
- Analysis posture: dual-track (static-first capability + data-driven validation when telemetry quality supports it).
- Boundary choice: Option A (canonical in-memory IR as source of truth; JSON/DOT/BPMN are projections/exports).
- First-class domains (long-term): control flow, information flow, material flow, and physical layout.
- First-class domains (long-term): control flow, information flow, material flow, physical layout, and staffing/people dynamics.
- Complexity ceiling: no execution semantics, no workflow runtime behavior, and no BPMN-equivalent scope creep.
- v0.1 syntax direction: support explicit `edges` plus decision-outcome shorthand, with deterministic canonicalization.
- v0.1 lane defaulting: lane kind may default to `default` when omitted.
- Metadata governance: keep v0.1 metadata minimal and defer broader taxonomy to v0.2.
- Queues are first-class in v0.1 via an explicit `queue` node kind (descriptive semantics only, non-executable).

## 1) Purpose

This note defines the minimum architectural and language decisions required to safely continue implementation of FLO v0.1.

Goals for this note:

- Freeze enough syntax and semantics to avoid rework in compiler/render/validation.
- Establish canonical IR as an in-memory Python model (not JSON-as-IR).
- Define export boundaries (`json`, `dot`, later BPMN subset) as projections.
- Define where Pydantic belongs and where it does not.
- Define interoperability posture for analysis packages (e.g., `sympy`, `statsmodels`).

## 2) v0.1 Scope (Simple Subset Only)

FLO v0.1 intentionally supports a constrained subset:

- Node kinds: `start`, `task`, `system_task`, `queue`, `decision`, `end`
- Directed edges with optional condition/outcome labels
- Optional lanes (`human`, `system`, `org_unit`, `external`)
- Optional typed metadata (small recommended set)
- Validation + DOT rendering + JSON export

Out of scope for v0.1:

- Full BPMN semantics
- Parallel gateways (`fork`, `join`) and token semantics
- Simulation runtime
- Process mining engine behavior
- Any execution scripting model

v0.1 notes on future dimensions:

- Physical layout, material movement, people movement (e.g., spaghetti map use-cases), and staffing constraints are first-class in the long-term language vision, but only minimal extension points are included in v0.1.

## 3) Canonical Architecture

### 3.1 Internal data flow

`FLO text/YAML` -> `Adapter parse/normalize` -> `Compiler` -> `Canonical IR (Python native)` -> `Validators` / `Analysis` / `Exporters`

Key rule: downstream components must consume canonical IR objects, not raw YAML mappings.

### 3.2 Canonical IR policy

The canonical IR is a Python object model. JSON is a serialization target only.

Required IR concepts in-memory:

- `Process` (id, name, version, metadata, nodes, edges, lanes)
- `Node` (id, kind/type, name, lane, metadata)
- `Edge` (source, target, condition/outcome, metadata)
- Optional helper views for SCC condensation (analysis layer)

### 3.3 Export/projection policy

Exports are projections from IR:

- `export json`: schema-aligned interchange artifact
- `export dot`: Graphviz projection
- `export bpmn-subset` (future): lossy/partial mapping explicitly documented

The IR object model must not include exporter-specific shape flags (for example, no schema mode booleans in domain objects).

## 4) Pydantic Placement Recommendations

Use Pydantic at **system boundaries**, not in algorithmic core.

Use Pydantic for:

- Adapter input models (parse/normalize external FLO docs)
- External API contracts (CLI request/response payloads if introduced)
- Export schema validation wrappers (optional convenience)
- Configuration and telemetry payload envelopes

Use dataclasses / simple typed classes for:

- Canonical IR domain model
- Graph algorithms (SCC, reachability, cycle/rework checks)
- Compiler intermediate transformations

Rationale:

- Keeps IR lightweight and algorithm-friendly
- Avoids mixing validation concerns into graph operations
- Makes adapters strict while preserving fast in-memory manipulation

## 5) Syntax Freeze Targets for v0.1

The following syntax areas must be explicitly frozen before implementation continues:

1. Required top-level keys (`spec_version`, `process`, `steps`, optional `lanes`, optional `metadata`)
2. Node declaration shape and defaults (required `id` and `kind`; optional `name`, `lane`, `metadata`)
3. Edge declaration mechanism:
   - explicit edge list and/or
   - decision outcome mapping shape
4. Conditional label syntax for decisions (`yes/no`, `else`, custom labels)
5. Typed metadata key conventions

Decision: v0.1 supports both explicit edge list and decision outcome shorthand. Compiler canonicalization to explicit edges is mandatory and deterministic.

## 6) Semantic Freeze Targets for v0.1

Must-have invariants:

- Exactly one `start` node
- One or more `end` nodes allowed
- All edge endpoints must resolve to declared nodes
- Node IDs globally unique and stable
- Decision nodes must have >=2 outgoing transitions (or explicit policy warning/error)
- Cycles allowed; reported explicitly by analysis
- Designed vs observed artifacts must remain distinct entities (no implicit merge of truth sources)

Decision default semantics (v0.1):

- FLO does not encode runtime waiting behavior.
- A decision node must resolve via explicit outgoing edges in the model.
- If an author needs a fallback path, they should model it explicitly (for example with an `else` outcome label or equivalent explicit edge policy).

Staffing/wait semantics guidance (v0.1):

- Delays caused by human availability are modeled as process facts, not runtime engine behavior.
- Authors should represent waiting states explicitly in the designed process (for example as review/queue/wait steps) and annotate them with staffing-related metadata.
- Observed wait-time from telemetry remains separate and is used for designed-vs-observed gap analysis.

Queue semantics (v0.1):

- `queue` is a first-class node kind used to represent buffering/wait states.
- Queue nodes are descriptive only; they do not imply executable scheduling or token semantics.
- Queue behavior assumptions (for example FIFO/priority) must be declared via metadata (`queue_policy`) when relevant.
- If queue capacity matters, authors may declare `buffer_capacity` metadata; omission means unspecified capacity, not infinite guaranteed capacity.
- Queue nodes should include ownership context (`lane` and/or `staff_role`) when human decision latency is the dominant cause of delay.

Queue validation policy (v0.1):

- Queue validation failures are **errors** (not warnings).
- A `queue` node must have at least one incoming edge and at least one outgoing edge.
- A `queue` node must include `metadata.queue_policy`.
- If `metadata.buffer_capacity` is present, it must be an integer >= 1.
- A queue node that violates any of the above fails `flo validate`.

Warnings (non-fatal in v0.1):

- Unreachable nodes
- Dead-end non-`end` nodes
- Untyped metadata keys
- Missing optional metadata keys (including staffing metadata outside required queue rules)

## 7) Canonicalization Rules (Compiler Contract)

Compiler output contract for v0.1:

- Emit canonical IR object graph deterministically from equivalent source forms
- Normalize shorthand syntax into explicit edges
- Preserve stable IDs for telemetry alignment and diffs
- Do not invent implicit runtime semantics

If source syntax is ambiguous, compiler must fail with actionable diagnostics instead of guessing.

## 8) Analysis Package Interoperability (sympy/statsmodels)

Recommendation: use canonical IR as the primary handoff model for internal adapters.

Posture for v0.1 and beyond:

- Static analyses remain available with no telemetry dependency.
- Observed-data analyses are enabled when event quality/volume/resolution are sufficient.
- Instrumentation quality improvement is treated as part of the FLO ecosystem learning path, not a hard prerequisite for basic modeling.

Pattern:

- `IR -> analysis adapter -> package-native structures`

Examples:

- `IR -> sparse matrices / vectors` for linear algebra pipelines
- `IR -> tabular feature frame` for statistical modeling

Use JSON export for:

- Persistence
- Interchange with external systems
- Reproducible snapshots

Do **not** make JSON the primary in-process interface to analysis libraries unless a library explicitly requires it.

## 9) CLI/Product Boundary (v0.1)

Recommended command posture:

- `flo validate <file>`: parse + compile + semantic/schema validation
- `flo compile <file>`: compile to canonical IR (in-memory), optional IR print/debug
- `flo export --format json|dot <file>`: projection/export only

This separation prevents conflating compilation with presentation format.

## 10) Immediate Implementation Sequence After Freeze

1. Finalize syntax + semantic examples in `examples/` (valid/invalid corpus)
2. Refactor compiler to emit canonical IR object model only
3. Move JSON shape generation into dedicated JSON exporter
4. Keep DOT renderer as exporter/projection from IR
5. Add conformance tests against frozen examples

## 11) Open Questions to Resolve Before Coding Further

1. What is the minimum typed metadata key set considered normative in v0.1?
2. For v0.1 extension points, should people movement be represented as:
   - a distinct flow type, or
   - metadata on edges/nodes pending v0.2 formalization?

Resolved in this revision:

- Edge-definition style: dual style with strict canonicalization (approved).
- Decision default handling: explicit modeled paths required; no implicit runtime wait semantics.
- Lane kind policy: optional; defaults to `default` when omitted.

## 13) v0.1 Metadata Recommendations (Minimal)

Given the current priorities, v0.1 should keep metadata intentionally small.

Recommended normative keys for v0.1:

- `activity_key` (node): stable telemetry alignment key
- `handoff` (edge): boolean or enum flag for cross-lane responsibility transfer
- `sla_target_seconds` (node or process): expected target duration in seconds
- `value_class` (node or process): lightweight classification for improvement analysis

Recommended staffing-related metadata keys for v0.1 (optional):

- `staff_role` (node): primary human role responsible for the step
- `staffing_level` (node): nominal number of people assigned/available
- `queue_policy` (node): simple policy tag (for example FIFO/LIFO/priority)
- `buffer_capacity` (node): intended maximum queued items/WIP limit (integer)
- `wait_reason` (node or edge): coarse reason classification for delay

Recommendation on strictness:

- Treat these keys as recommended (not required) in v0.1.
- Unknown metadata keys remain allowed with warnings.
- Missing metadata keys are warnings in v0.1 unless covered by explicit queue validation errors.
- Promote stricter metadata contracts in v0.2 after conformance examples stabilize.

## 14) First-Class People/Staffing Principle

FLO treats people and staffing as first-class modeling concerns, not incidental annotations. This is required because human decision latency and staffing constraints are often primary drivers of process delay and variation.

Design implications:

- The language must be able to represent ownership, staffing, and human wait points in the designed model.
- The analytics layer must quantify staffing-related effects (queueing, wait time, handoff delay) from observed data when available.
- Human-readable syntax remains mandatory; staffing constructs must stay authorable in plain text and avoid workflow-engine semantics.

## 15) Queue Modeling Examples (v0.1)

Valid (explicit human decision queue):

```yaml
steps:
   - id: submit_request
      kind: task
      lane: operations
   - id: manager_review_queue
      kind: queue
      lane: finance
      metadata:
         staff_role: manager
         queue_policy: FIFO
         buffer_capacity: 25
         wait_reason: pending_human_decision
   - id: approve_decision
      kind: decision
      lane: finance
      outcomes:
         approved: execute_payment
         rejected: notify_requestor
edges:
   - source: submit_request
      target: manager_review_queue
   - source: manager_review_queue
      target: approve_decision
```

Invalid (queue implied but not modeled):

```yaml
steps:
   - id: approve_decision
      kind: decision
      metadata:
         wait_reason: pending_human_decision
```

Reason invalid in v0.1: human wait is claimed but no explicit queue/wait path is represented in structure.

## 16) Decision Log (Doc Governance)

Recorded decisions:

- **D-001**
   - Decision: Designed and observed process models remain separate and are linked through explicit alignment/conformance.
   - Rationale: Prevents truth-source conflation and supports dual-track analysis quality.
   - Consequences: Compiler/IR treat designed and observed artifacts as distinct structures.
   - Effective version: v0.1

- **D-002**
   - Decision: Option A boundary adopted — canonical in-memory IR is source of truth; JSON/DOT/BPMN are export projections.
   - Rationale: Preserves clean internals and supports long-term analytics adapters.
   - Consequences: No JSON-as-IR internals; exporters own transport shape.
   - Effective version: v0.1

- **D-003**
   - Decision: Queue is first-class in v0.1 via `queue` node kind with descriptive (non-executable) semantics.
   - Rationale: Human decision and staffing delays are core process constraints.
   - Consequences: Queue structural validation failures are errors.
   - Effective version: v0.1

- **D-004**
   - Decision: Lane kind defaults to `default` when omitted.
   - Rationale: Keeps syntax lightweight while supporting generic organizational partitions.
   - Consequences: Validators should normalize missing lane kind to `default`.
   - Effective version: v0.1

Template for future decisions:

When these open questions are resolved, append a short decision record block:

- Decision:
- Rationale:
- Consequences:
- Effective version:

Keeping these records in this file avoids spec drift while implementation proceeds.

## 17) Open Issue Register

- **OI-001: People movement representation in v0.1/v0.2 bridge**
   - Question: represent people movement as a distinct flow type, or as metadata on nodes/edges until formalized?
   - Current status: open
   - Target resolution: before v0.2 syntax freeze
