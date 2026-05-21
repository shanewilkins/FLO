# Swimlane

Purpose: define what a swimlane diagram means in FLO and which behavior is part
of its normative contract.

## Intent

A swimlane diagram is FLO's responsibility-organized process visualization.

It presents the canonical process graph while grouping steps by lane so a
reader can understand both process sequence and where work is performed across
roles, departments, systems, or other lane-like partitions.

## Required inputs

A swimlane diagram depends on:

1. Canonical FLO process structure.
2. Lane assignments when present.
3. Optional subprocess and layout metadata.

When lane assignments are incomplete, FLO may still render the process, but the
responsibility view becomes partial.

## Normative characteristics

A swimlane diagram in FLO must satisfy the following characteristics:

1. Control-flow preservation
   - The diagram still represents the canonical process graph rather than a
     separate lane-only abstraction.

2. Lane-based grouping
   - Nodes with lane assignments must be organized by lane so responsibility
     boundaries are visible.

3. Usable handling of unlaned nodes
   - Nodes without lane assignments must remain renderable even when they do
     not belong to a lane grouping.

4. Cross-lane flow visibility
   - Edges that cross lane boundaries must remain understandable as transitions
     between responsibility surfaces.

5. Optional subprocess projection
   - Subprocess expansion or collapse may change presentation density but must
     not change process meaning.

## Non-goals

A swimlane diagram is not:

- a publication-first document surface
- a movement-analysis map
- a guarantee of organizational correctness beyond the lane metadata provided
- a substitute for core semantic validation

## Relationship to other documents

- Diagram meaning is defined here.
- Renderer structure and lane-rendering boundaries belong in
  `docs/design/swimlane_renderer_design.md`.
- Core process semantics belong in `docs/specs/core_language.md`.
