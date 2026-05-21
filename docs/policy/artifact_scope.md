# FLO Artifact Scope Policy

Purpose: define which kinds of artifacts belong in FLO and which should live in
downstream analysis packages such as `lss4py`.

## Core rule

FLO is a structured process description language and projection surface.

An artifact belongs in FLO only if it is a direct projection, summary, or
lightly enriched view of the canonical FLO process model.

An artifact should live in `lss4py` or another downstream analysis package if
it requires a distinct analytical framework, problem-specific scoring model,
causal model, customer-preference model, or other semantics not already part of
the canonical FLO process description.

## FLO-owned artifact classes

These artifact classes fit FLO's scope:

1. Core process projections
   - Direct views of the canonical process model.
   - Examples: flowchart, swimlane, SPPM.

2. Process-native movement and flow views
   - Views derived from process structure plus declared movement, layout, or
     flow metadata.
   - Examples: spaghetti map, value stream map.

3. Structured process summaries
   - Summaries that remain faithful to declared process entities and metadata.
   - Examples: IPO or SIPOC-style summaries when suppliers, inputs, outputs,
     and customers are explicitly modeled or cleanly derivable.

## Downstream analysis artifact classes

These artifact classes do not belong in FLO's core scope:

1. Causal analysis tools
   - Examples: Ishikawa diagrams, 5 Whys chains, cause-and-effect trees.

2. Prioritization and selection tools
   - Examples: prioritization matrices, effort-impact grids, ranking models.

3. Customer-preference or product-analysis tools
   - Examples: Kano analysis.

4. Problem-framing and improvement-method artifacts
   - Examples: A3 problem-analysis surfaces, CTQ trees, FMEA-style scoring and
     ranking surfaces.

## Decision test

Use this test when deciding whether a new artifact belongs in FLO:

1. Can it be emitted faithfully from the canonical FLO process model and its
   declared metadata?
2. Does it remain primarily a process description or process projection rather
   than a separate analytical method?
3. Can it be specified without introducing a new methodological worldview into
   the core language?

If the answer to any of these is no, the artifact should default to `lss4py`.

## Consequence for new proposals

When proposing a new artifact for FLO, the proposal should explicitly state:

- whether it is a direct process projection, a structured summary, or a derived
  analysis view
- which parts are already present in the canonical process model
- which additional metadata, if any, are required

If the proposal depends on external scoring, causal reasoning, prioritization,
or customer-analysis semantics, it should be treated as out of scope for FLO.
