# Process Map

Purpose: define the shared normative semantics for FLO's rich process-map
family.

## Intent

A process map is FLO's rich process-graph visualization family.

It presents the canonical process graph with a broader visual and semantic
surface than a minimal flowchart. A process map may add richer shapes,
annotations, continuation conventions, and analytics-oriented adornments, but
it still derives its meaning from the same underlying process structure.

In the current specification set, `sppm` and `swimlane` are process-map
variants.

## Required inputs

A process map is derived from canonical FLO process structure:

- process metadata
- nodes and edges
- decision outcomes and rework semantics
- optional subprocess relationships
- optional lane assignments when a variant needs them
- optional approved analysis or summary metadata when a variant supports it

Additional presentation metadata may refine rendering, but it does not replace
the canonical process graph as the semantic source.

## Normative characteristics

A process map in FLO must satisfy the following characteristics:

1. Process-graph preservation
   - The diagram represents the canonical FLO process graph rather than an
     alternate model.

2. Rich node-kind visibility
   - The visual treatment must preserve distinctions between meaningful node
     kinds and support a broader shape vocabulary than a minimal flowchart when
     the variant requires it.
   - This includes accepted control-flow kinds such as `decision`, `queue`,
     `wait`, `subprocess`, `parallel_split`, and `parallel_join`.

3. Explicit branching and rework visibility
   - Directed edges, outcomes, and rework-oriented flow must remain legible so
     the reader can understand process logic, not just local sequencing.
   - Handoff-bearing transitions should remain readable as distinct semantic
     relations when the variant surfaces them.

4. Variant-specific structural grouping
   - A process-map variant may organize the same process graph by lanes,
     sections, continuation surfaces, or similar grouping devices, but these
     devices must not change process meaning.

5. Analytics-compatible annotation surface
   - Approved analysis or summary information may be shown as annotations when
     the variant supports it, but those annotations must not redefine the core
     process semantics.

6. Optional subprocess projection
   - Subprocess expansion, collapse, or related projection choices may change
     presentation density but must not change underlying process meaning.

## Non-goals

A process map is not:

- a simulation output
- a facility layout map
- a free-form reporting canvas for arbitrary KPIs
- a substitute for the canonical IR or core-language semantics

## Relationship to other documents

- Shared rich process-map semantics are defined here.
- Minimal control-flow semantics belong in `flowchart.md`.
- Variant-specific meaning belongs in `sppm.md` and `swimlane.md`.
- Core process semantics belong in `core_language.md`.
- Implementation strategy belongs in `docs/design/`.
