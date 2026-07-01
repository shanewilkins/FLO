# Flowchart

Purpose: define what a flowchart means in FLO and which behavior is part of its
normative contract.

## Intent

A flowchart is FLO's intentionally minimal control-flow visualization.

It presents the canonical process graph directly, with the smallest practical
semantic and visual surface needed to make step sequence, branching, and
rework readable. Its design target is closer to a lightweight Mermaid-style
diagram than to FLO's richer process-map family.

## Required inputs

A flowchart is derived from canonical FLO process structure:

- nodes and edges
- meaningful node kinds
- decision outcomes and rework edges when present
- optional subprocess relationships
- optional layout settings that affect orientation or wrapping

Flowcharts should not require richer process-map annotations, lane metadata, or
publication metadata to remain useful.

## Normative characteristics

A flowchart in FLO must satisfy the following characteristics:

1. Control-flow-first representation
   - The diagram represents the canonical process graph directly.

2. Minimal node-kind visibility
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

6. Constrained presentation surface
   - The diagram should avoid richer process-map affordances such as lane
     partitioning, analytics-oriented annotations, dense continuation surfaces,
     or publication framing.

## Non-goals

A flowchart is not:

- a lane-responsibility diagram
- a rich process map such as `sppm` or `swimlane`
- a movement or facility layout map
- a substitute for the structural IR contract

## Relationship to other documents

- Diagram meaning is defined here.
- Shared rich process-map semantics belong in `process_map.md` rather than
   here.
- Renderer structure and shared routing boundaries belong in
  `docs/design/renderers/flowchart.md`.
- Core process semantics belong in `docs/specs/core_language.md`.
