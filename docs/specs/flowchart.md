# Flowchart

Purpose: define what a flowchart means in FLO and which behavior is part of its
normative contract.

## Intent

A flowchart is FLO's baseline control-flow visualization.

It presents the canonical process graph directly, with minimal additional
semantic layering. Its job is to make step sequence, branching, and rework easy
to read without introducing publication framing, movement analysis, or lane
responsibility as the primary organizing principle.

## Required inputs

A flowchart is derived from canonical FLO process structure:

- process metadata when needed for labels or graph metadata
- nodes and edges
- optional subprocess relationships
- optional layout settings that affect orientation or wrapping

## Normative characteristics

A flowchart in FLO must satisfy the following characteristics:

1. Control-flow-first representation
   - The diagram represents the canonical process graph directly.

2. Node-kind visibility
   - The visual treatment must preserve meaningful distinction between node
     kinds such as `start`, `task`, `decision`, and `end`.

3. Edge-based sequencing
   - Directed edges must communicate process sequence and branching.

4. Rework visibility
   - Backward or rework-oriented flow should remain visually distinguishable
     from ordinary forward flow.

5. Optional subprocess projection
   - The diagram may expand or collapse subprocess content, but it must not
     change the underlying process meaning.

## Non-goals

A flowchart is not:

- a lane-responsibility diagram
- a publication-first controlled document
- a movement or facility layout map
- a substitute for the structural IR contract

## Relationship to other documents

- Diagram meaning is defined here.
- Renderer structure and shared routing boundaries belong in
  `docs/design/flowchart_renderer_design.md`.
- Core process semantics belong in `docs/specs/core_language.md`.
