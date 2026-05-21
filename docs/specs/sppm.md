# Standard Process Procedure Map (SPPM)

Purpose: define what an SPPM means in FLO and which behavior is considered
part of the normative diagram contract.

## Intent

An SPPM is FLO's publication-oriented process map.

It presents a process as a structured, reader-friendly diagram intended for
operational communication, work instruction, review, and controlled publication.
Compared with a basic flowchart, an SPPM favors legibility, presentation
discipline, and document-style framing over minimal rendering.

## Required inputs

An SPPM is derived from canonical FLO process structure:

- process metadata
- nodes and edges
- labels and outcomes
- optional publication metadata
- optional analysis or metadata-backed summary metrics

The renderer may use additional presentation metadata, but the underlying
process graph remains the semantic source.

## Normative characteristics

An SPPM in FLO must satisfy the following characteristics:

1. Process-first representation
   - The diagram represents the canonical process graph, not an alternate model.

2. Publication-oriented framing
   - The diagram may include headers, footers, captions, legends, or related
     publication surfaces when metadata supplies them.

3. Legible structured layout
   - The layout should prioritize readable node labels, stable routing, and
     intelligible continuation handling for dense maps.

4. Explicit decision visibility
   - Decision points and their outcomes must remain visually distinguishable so
     branching logic is clear to a reader.

5. Optional metrics as annotations
   - Summary metrics may be shown when supplied or derivable from approved FLO
     analysis surfaces, but the SPPM does not redefine process semantics.

## Non-goals

An SPPM is not:

- a simulation output
- a facility layout map
- a process mining timeline
- a free-form reporting canvas for arbitrary KPIs

## Relationship to other documents

- Diagram meaning is defined here.
- Renderer decomposition and refactor boundaries belong in
  `docs/design/sppm_renderer_design.md`.
- Structural IR contract belongs in `schema/flo_ir.json`.
- Core process semantics belong in `docs/specs/core_language.md`.
