# FLO Design Documents

Status: accepted

This directory holds explanatory design material for FLO.

For the top-level documentation map and authority order, start with
`docs/README.md`.

Design documents explain architecture, implementation strategy, refactor plans,
and historical rationale. They do not override policy, specs, or schema.

## Directory Layout

Use these subdirectories for fast navigation.

- `docs/design/adr/`
  - architecture decision records with accepted or rejected directions
- `docs/design/renderers/`
  - renderer-family implementation notes and renderer boundaries
- `docs/design/history/`
  - retained historical context that is not normative

The top level of `docs/design/` is reserved for active cross-cutting design
notes, migration plans, and taxonomy notes that span multiple components.

## Review prompts

- [Shared lenses and evidence rules](review_lenses.md): fourteen perspectives,
  including book, lss4py and mpi-theme ownership and compatibility.
- [Code and ecosystem review](code_ecosystem_review_prompt.md): engineering
  findings, terminology, duplicated responsibility and consumer compatibility.
- [Release quality gate](release_quality_gate_prompt.md): exact-candidate
  release acceptance, scoring, packaging and publication evidence.

## Architecture acceptance before release

- [Architecture validation results](architecture_validation.md): completed
  assessment, closure of three findings, and candidate acceptance under TR-118.
- [Architecture validation slice](architecture_validation_plan.md): completed
  assessment scope and disposition.
- [Layout finalization ADR](adr/render_layout_finalization.md): accepted ownership
  clarification, implemented by R1–R3b.
- [Release architecture integrity policy](../policy/release_architecture_integrity.md):
  authoritative acceptance gate and known-good baseline requirements for every release.

## White Belt acceptance evidence

- [Release closure plan](white_belt_release_plan.md): ordered release gates,
  completed candidate gates and remaining release-cut actions.
- [Candidate acceptance](white_belt_candidate_acceptance.md): immutable revision,
  clean platform results, finding dispositions, and artifact identities.


- [Semantic pipeline audit](white_belt_semantic_audit.md): completed language,
  schema, public API, and canonical exchange audit for the semantic slice of TR-114.

## Book-aligned breaking refactor

- [Implementation and phase status](book_aligned_contract_refactoring_plan.md):
  reconciled phase prerequisites and explicit remaining work.
- [Failure and defect ledger](book_aligned_refactor_failure_ledger.md): all 89
  original failures, verified closures, and newly exposed implementation defects.
- [Accepted contract](../specs/book_aligned_contract.md): book terminology,
  measurement/evidence shapes, and field ownership.

## Structural integrity follow-up

- [Structural integrity inventory](structural_integrity_inventory.md): existing
  graph protections, reproduced gaps, candidate lint rules and NetworkX scope.

- [Structural integrity refactoring plan](structural_integrity_refactoring_plan.md):
  completed identity/reference fixes, shared NetworkX graph facts, cycle
  inspection and test naming cleanup.

## Next-sprint implementation planning

- [Pydantic source and render inputs](adr/pydantic_source_and_render_inputs.md):
  historical source/render-input decision, superseded for source syntax by the
  book-aligned contract; shared render-option normalization remains applicable.
- [Quantity validation and units](adr/quantity_validation_and_units.md): completed
  configuration consolidation, spatial Pint trial, shared duration conversion,
  and measured resource canonical equivalence without changing source syntax.
- [Consistent diagnostic delivery](diagnostic_delivery_plan.md): implemented 0.4
  stabilization work for UR-086 and TR-117, including warning aggregation,
  severity-aware success, and the missing-timing use case.

## Authority Boundary

Design documents are explanatory. ADRs record durable rationale but do not
override the authoritative domain identified in `docs/GOVERNANCE.md`.

If a design note appears to define normative behavior, move that behavior into
the appropriate requirement, specification, schema, or policy and link to it.

## Document Types

Common document types in this directory:

- architecture notes: broad implementation boundaries and historical decisions
- ADRs: explicit decisions with accepted or rejected options
- taxonomy notes: artifact families, ownership, and lifecycle guidance
- renderer design notes: implementation strategy for one renderer family
- migration plans: phased change plans for accepted directions
- historical notes: retained background context that is no longer authoritative

## Status Guidance

ADRs use the controlled states `proposed`, `accepted`, and `superseded`.

Ordinary design notes may carry descriptive status text when it helps readers,
but governance does not require or validate a status header on every note.
Completed plans should move to history or clearly link to the current contract.

## Naming Guidance

Prefer file names that reveal purpose without opening the file:

- use concise topic names under `docs/design/renderers/` for renderer notes
- use concise topic names under `docs/design/adr/` for decision records
- use `*_migration_plan.md` for phased implementation plans at design root
- avoid near-duplicate names for overlapping topics
- avoid using `spec` in this directory unless the file is explicitly
  non-normative and says so

## Practical Lookup Guide

If you need to answer one of these questions:

- "What governs authoritative truth?" -> `docs/policy/`
- "What must FLO deliver, and by when?" -> `docs/requirements/`
- "What does this FLO artifact mean?" -> `docs/specs/`
- "How is this implemented or why was it designed this way?" -> `docs/design/`
- "What is the serialized contract?" -> `schema/`

## Render Platform Document Set

The render-platform material is intentionally split across three documents.

- `adr/render_stack_elk_svg_typst.md`
  - why the decision was made and which alternatives were accepted or rejected
- `render_platform_target_architecture.md`
  - the intended steady-state architecture and layer boundaries
- `render_platform_migration_plan.md`
  - the phased path from the current implementation to the target architecture

- `layout_canvas_boundary_contract.md`
  - one-page layout-to-canvas handoff contract and ELK/SVG ownership boundary

This split is deliberate. Keep the ADR short and decision-focused, keep the
target architecture focused on the steady state, and keep implementation phases
in the migration plan instead of duplicating them across all three files.

## Artifact Taxonomy

`artifact_taxonomy.md` is the current design-level guide to what artifact
families FLO produces, which ones are canonical versus derived, and which layer
owns each artifact family.

## Language Primitive Taxonomy

`language_primitive_taxonomy.md` defines the accepted hierarchy of process
 primitives, relations, organizing structures, and compiled forms for FLO's
 process-first language direction.

## Design Index

### Decisions

- `adr/governance_v2.md`
- `adr/language_primitive_taxonomy.md`
- `adr/render_stack_elk_svg_typst.md`

### Renderer Design

- `renderers/boundaries.md`
- `renderers/spaghetti.md`
- `renderers/sppm.md`
- `renderers/sppm_layout_enhancement.md`
- `renderers/swimlane.md`
- `renderers/value_stream.md`

### Active Cross-Cutting Design

- `artifact_taxonomy.md`
- `language_primitive_taxonomy.md`
- `layout_canvas_boundary_contract.md`
- `publication_model.md`
- `render_intent_schema.md`
- `render_platform_migration_plan.md`
- `render_platform_target_architecture.md`
- `typed_metadata.md`
- `wait-time-vs-changeover-time-semantics.md`

### Historical Context

- `history/IR.md`
- `history/ontology.md`
- `history/v0_1_architecture_note.md`

## Current Cleanup Notes

- `docs/design/history/IR.md` is retained background material and should not be treated
  as normative over `docs/specs/core_language.md`.
- `docs/README.md` is the entrypoint for repository-wide documentation
  navigation before drilling into design, policy, or specs.
