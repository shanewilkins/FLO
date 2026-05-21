# Standard Process Procedure Map (SPPM)

Purpose: define what an SPPM means in FLO and which behavior is considered
part of the normative diagram contract.

## Intent

An SPPM is FLO's default rich process-map variant.

It presents a process as a structured, reader-friendly diagram intended for
operational communication, work instruction, review, and continuous-improvement
analysis. Compared with a minimal flowchart, an SPPM favors richer process
objects, denser but controlled annotation, and stronger legibility rules for
complex maps.

## Required inputs

An SPPM depends on:

1. The rich process-map semantics defined in `process_map.md`.
2. Optional analysis or metadata-backed summary metrics.
3. Optional presentation metadata that refines, but does not replace, the
  underlying canonical process graph.

## Normative characteristics

An SPPM in FLO must satisfy the following characteristics:

1. Process-map-first representation
   - The diagram represents the canonical process graph and richer process-map
     semantics, not an alternate model.

2. Rich process-object vocabulary
   - The diagram may use a broader shape and annotation vocabulary than a
     minimal flowchart when needed to express approved FLO process-map
     semantics and LSS-oriented analysis surfaces.

3. Legible structured layout
   - The layout should prioritize readable node labels, stable routing, and
     intelligible continuation handling for dense maps.

4. Explicit decision visibility
   - Decision points and their outcomes must remain visually distinguishable so
     branching logic is clear to a reader.

5. Optional metrics as annotations
   - Summary metrics may be shown when supplied or derivable from approved FLO
     analysis surfaces, but the SPPM does not redefine process semantics.

6. Publication composition is adjacent, not defining
   - Headers, footers, captions, and other page furniture may accompany an
     SPPM in publication workflows, but those surfaces are not the core
     defining semantic difference between SPPM and other process-map variants.

## Non-goals

An SPPM is not:

- a simulation output
- a facility layout map
- a process mining timeline
- a free-form reporting canvas for arbitrary KPIs
- a minimal flowchart

## Relationship to other documents

- Diagram meaning is defined here.
- Shared rich process-map semantics belong in `process_map.md`.
- Renderer decomposition and refactor boundaries belong in
  `docs/design/sppm_renderer_design.md`.
- Structural IR contract belongs in `schema/flo_ir.json`.
- Core process semantics belong in `docs/specs/core_language.md`.
