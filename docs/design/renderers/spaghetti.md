# Spaghetti Renderer Design

Status: accepted

## Purpose

Define the current implementation boundaries for FLO's movement-oriented,
FLO-owned direct-SVG renderer.

Normative diagram meaning remains in `docs/specs/spaghetti_map.md`.

## Current rendering path

Spaghetti rendering follows this pipeline:

1. infer material and people movements from canonical IR
2. aggregate movements into location-pair routes
3. extract declared locations, spatial coordinates, and optional boundaries
4. project explicit coordinates into canvas geometry
5. emit a standalone FLO-owned SVG artifact

The renderer does not use a graph-layout fallback. Graphviz is deprecated and
must not be reintroduced to infer missing positions.

## Channel and aggregation controls

The renderer supports:

- `material`, `people`, or `both` movement channels
- aggregate people routes by location pair
- worker-level people routes when worker identity is available

Movement inference and aggregation remain analysis concerns. SVG emission
consumes their results and does not recalculate process semantics.

## Spatial contract

Rendered route endpoints require explicit numeric spatial coordinates.

The current direct-SVG implementation fails with an actionable render error if
any rendered location lacks coordinates. Rectangle and polygon boundaries are
optional and affect the canvas when supplied.

The 0.3 planned implementation partitions selected movement routes into
renderable and omitted sets. Default mode emits the renderable set, a stable
stderr warning, and a visible partial-map notice. Strict mode fails when the
omitted set is non-empty. Default mode also fails when the renderable set is
empty.

Missing IDs and counts remain deterministic. No mode assigns synthetic
coordinates or invokes graph layout; a deprecated layout backend is not an
acceptable fallback.

## Location presentation

Location kind controls semantic SVG shape and styling. Unknown kinds keep the
default location treatment. Route groups retain channel, source, target, item,
worker, and aggregation information where available so artifacts remain
inspectable and testable.

## Current module boundaries

- `src/flo/render/_svg_spaghetti.py`
  Direct-SVG projection and artifact emission.
- `flo.compiler.analysis`
  Movement inference and aggregation.
- `src/flo/render/_svg_shared_primitives.py`
  Shared SVG definitions where the semantics are renderer-neutral.

## Verification

Artifact-contract tests cover:

- channel selection
- worker and aggregate people modes
- route labels, titles, styles, and counts
- location-kind shapes
- rectangle and polygon boundaries
- deterministic missing-spatial failure

The target 0.3 implementation coverage adds:

- mixed positioned and unpositioned endpoints in default partial mode
- stable omitted location and route counts
- visible partial-map notice
- strict-mode failure before artifact emission
- default-mode failure when no complete route remains

## Extension rules

- Keep movement inference outside the renderer.
- Keep explicit spatial semantics separate from graph layout.
- Implement the accepted partial and strict missing-spatial policy in 0.3.
- Do not add deprecated backend dependencies.
