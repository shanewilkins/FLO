# Value Stream Map

Purpose: define what a lean-style value stream map means in FLO and which
behavior is part of its normative contract.

Lifecycle: planned for 0.3 as the maintained `value_stream` SVG renderer;
stable-tier promotion is required by 1.0. It is not supported by the current
0.1.x runtime.

## Intent

A value stream map is FLO's lean-oriented flow visualization for showing how
work, information, and material move through a process system.

Unlike a plain flowchart, a value stream map is not only about control-flow
order. It is intended to help a reader understand the relationship between
process steps, information signals, material movement, waiting, and overall
flow efficiency.

## Required inputs

A value stream map depends on:

1. Canonical FLO process structure.
2. Information-flow semantics or metadata when information movement is to be
   shown explicitly.
3. Material-flow semantics or metadata when material movement is to be shown
   explicitly.
4. Optional timing, queue, inventory, or summary metrics when lean analysis
   annotations are desired.

When one of the two flow surfaces is incomplete, FLO may still render a partial
value stream map, but it should make the omission clear rather than silently
pretending the missing surface does not exist.

## Normative characteristics

A value stream map in FLO must satisfy the following characteristics:

1. Dual-flow representation
   - The diagram must support representation of both information flow and
     material flow within the same map.

2. Process-anchored meaning
   - Information and material flows must remain anchored to the canonical FLO
     process model rather than becoming an unrelated diagram.

3. Distinguishable flow surfaces
   - Information flow and material flow must remain visually or structurally
     distinguishable so a reader can tell which surface is being shown.

4. Lean-analysis orientation
   - The diagram may surface waiting, inventory, queue, lead-time, processing
     time, or related lean annotations when supplied or derivable from approved
     analysis inputs.

5. Graceful partial rendering
   - If only information flow or only material flow is available, the map may
     render a partial view, but it should preserve the distinction between what
     is known and what is absent.

## Non-goals

A value stream map is not:

- merely a restyled flowchart
- a facility-layout or travel-path diagram
- a publication-first work instruction surface
- a standalone simulation of throughput or scheduling behavior

## 0.3 delivery contract

The 0.3 release adds the value-stream-map surface as one coherent capability:

- public diagram identifier: `value_stream`
- render backend: direct SVG over the accepted ELK/FLO-owned-SVG platform where
  layout is required
- capability-matrix entry and early unsupported-pair diagnostics
- deterministic fixtures for full dual-flow, information-only,
  material-only, and missing-optional-metric models
- user documentation covering inputs, partial-data diagnostics, and the
  distinction from spaghetti and control-flow views

The renderer enters the maintained tier in 0.3 and must meet the stable-tier
gates by 1.0. Implementation, tests, capability declarations, and user-facing
documentation ship together; the normative contract does not treat a schema
placeholder alone as delivery.

## Relationship to other documents

- Diagram meaning is defined here.
- Core process semantics belong in `docs/specs/core_language.md`.
- Spaghetti-map semantics belong in `docs/specs/spaghetti_map.md` when the
  concern is physical movement path visualization.
- Future implementation or renderer-boundary notes should live in
  `docs/design/`.
- Release ownership and tier gates live in `docs/ROADMAP.md`.
