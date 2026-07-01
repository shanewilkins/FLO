# ADR: Render Stack Direction

Status: accepted

## Context

FLO currently treats rendering largely as Graphviz DOT emission plus optional
Graphviz process invocation and SVG postprocessing.

That design was sufficient for early renderer work, but it is now under strain:

- Graphviz-specific routing details have leaked into shared renderer logic.
- SVG postprocessing is compensating for backend limitations.
- SPPM work increasingly needs true publication behavior rather than a single
  oversized graph.
- FLO also needs standalone graphics suitable for reports, notebooks, slides,
  and documentation.

Additional constraints agreed in May 2026:

- no browser runtime
- no commercial rendering engine
- likely need for true document composition

## Decision

FLO will adopt the following target render stack:

- ELK for graph layout and routing where diagram families need algorithmic
  placement
- FLO-owned SVG emission as the canonical standalone graphics path
- Typst as the publication compositor for page-aware document output

Graphviz remains supported only as a migration backend and optional fallback,
not as the long-term architectural center of the renderer platform.

## Decision Details

### Why ELK

ELK is a better fit than Graphviz for explicit layout constraints, ports,
hierarchy, and routed edge geometry.

ELK is chosen as a layout engine, not as a publication or rendering engine.

### Why FLO-owned SVG

SVG is the best canonical graphics artifact for FLO because it:

- embeds cleanly in notebooks, slides, reports, and web-adjacent contexts
- preserves vector fidelity
- can be converted to PNG or PDF when needed
- keeps diagram semantics and styling under FLO control

### Why Typst

Typst is chosen for document composition because FLO needs a true page model in
publication mode but should not build a full compositor itself.

Typst is responsible for page composition, not graph layout.

## Explicitly Rejected Alternatives

### Stay Graphviz-first

Rejected as the target architecture.

Reason:

- acceptable as an interim backend
- not acceptable as the long-term center for routing plus publication
- continues the current postprocess and workaround trend

### Emit LaTeX instead of DOT

Rejected as the primary diagram backend.

Reason:

- LaTeX is a document system, not a strong general graph layout engine
- TikZ/PGF would make diagram generation harder, not cleaner
- it would worsen standalone embeddable graphics workflows

LaTeX-like document systems may still be considered later as publication
consumers, but not as FLO's primary renderer backend.

### Browser-native rendering

Rejected due to the explicit no-browser-runtime constraint.

### Commercial diagram engines

Rejected due to the explicit no-commercial-licensing constraint.

## Consequences

Positive consequences:

- clearer ownership boundaries between semantics, layout, rendering, and pages
- better long-term routing control than Graphviz
- standalone graphics remain first-class rather than side effects of document
  generation
- true publication output can evolve without turning FLO into LaTeX-by-hand

Negative consequences:

- FLO still owns meaningful rendering work, especially SVG emission
- migration will take multiple phases
- some diagram families will temporarily straddle Graphviz and the new stack

## Implementation Posture

The migration should be incremental.

- Keep Graphviz working while extracting backend-neutral contracts.
- Move diagram families independently rather than attempting a flag day.
- Treat spaghetti and SPPM differently from flowchart/swimlane when their
  semantics demand it.

## Follow-On Documents

- `docs/design/render_platform_target_architecture.md`
- `docs/design/render_platform_migration_plan.md`
- `docs/design/publication_model.md`