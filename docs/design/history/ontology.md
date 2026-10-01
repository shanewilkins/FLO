# FLO Ontology (Historical Draft)

Status: historical

This note is retained as background context only.
Normative semantics live in `docs/specs/core_language.md` and authoritative structural contracts live in `schema/flo_ir.json`.
Its terminology predates the accepted process-first `item` and `resource` taxonomy and the current explicit `parallel_split`, `parallel_join`, and transition-level `handoff` semantics.

## Purpose

This historical draft captured an earlier attempt to define a compact FLO vocabulary.
It is still useful for understanding why the project kept a graph-shaped IR, even though the accepted source model is now process-first.

## Historical core concepts

- Process: a named model describing a sequence of work for achieving an outcome.
  Example attributes included `id`, `name`, `version`, owner references, and freeform metadata.
- Step or node: a discrete element in a process graph.
  Earlier drafts centered `start`, `task`, `decision`, `end`, and future `subprocess` forms.
- Transition or edge: a directed connection between two steps.
  Earlier drafts emphasized `source`, `target`, and optional outcome or label fields.
- Lane: a partitioning construct for organizational responsibility such as role, team, or system.
- Outcome or condition: a named label on an outgoing transition.
- Artifact: a document, data object, or input or output produced or consumed by a step.
- Event: a runtime or telemetry observation with fields such as `case_id`, `activity_key`, and `timestamp`.
- Case: a single execution instance of a process.

## Historical IR framing

At the historical IR level, a process was framed as a pair of `nodes` and `edges`.
That representation mapped directly to YAML and to projections such as DOT and other graph views.

## Historical DAG versus cycles notes

- Idealized view: a process as a DAG simplified several static analyses.
- Reality: real business processes commonly contain cycles such as rework loops, retries, and iterative approvals.
- Historical approach: keep the canonical IR as a directed graph and use SCC condensation when an acyclic view is required.

## Historical design guardrails

- No implicit looping constructs with unbounded counters or embedded scripts.
- Keep node and edge metadata small and typed where possible.
- Require each feature to map deterministically to the IR.

## Historical metrics examples

- `sla_target_seconds` on node metadata.
- `value_class` on process or node metadata.
- `handoff` on edge metadata.

## Historical telemetry note

The historical telemetry mapping centered a minimal event schema with `case_id`, `activity_key`, and `timestamp`.
`activity_key` was expected to align with a stable node identifier.

## Historical next steps

The draft originally pointed toward a formal IR spec, examples, and SCC-based analysis fixtures.
Those concerns are now superseded by the accepted spec, schema, and fixture corpus elsewhere in the repository.

---

Document version: draft (v0.0)
