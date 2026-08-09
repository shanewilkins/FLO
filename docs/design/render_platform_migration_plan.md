# Render Platform Migration Plan

Status: draft

Plan state: in progress

## Purpose

Track the remaining work from FLO's current ELK-backed, FLO-owned direct-SVG
platform to the accepted steady state:

- ELK for graph layout and routing
- FLO-owned SVG for standalone graphics
- Typst for page-aware publication composition

The architecture decision is accepted in
`docs/design/adr/render_stack_elk_svg_typst.md`. This plan tracks delivery and
does not reopen that decision.

## Current state

The renderer platform has moved beyond the Graphviz-first implementation.

Current facts:

- SVG is the only public render backend.
- Swimlane and SPPM use FLO-owned SVG emission over the ELK request/result seam.
- Spaghetti uses FLO-owned SVG emission from explicit spatial coordinates.
- Backend-neutral layout, artifact, diagnostics, and publication contracts
  exist in code.
- Shared SVG primitives provide common node, edge, marker, typography, and lane
  behavior.
- Graphviz is deprecated and has no active renderer module or backend-selection
  path.
- Flowchart was removed with the 0.2 renderer consolidation.
- Publication-plan foundations exist, but Typst composition and full multi-page
  SPPM publication are not complete.

Historical Graphviz and DOT references belong in changelogs, ADR context, or
historical notes only. Active renderer guidance must not recommend them as a
fallback or extension point.

## Migration principles

- Keep diagram semantics independent from layout and canvas implementation.
- Keep layout requests and results backend-neutral at renderer boundaries.
- Keep SVG emission deterministic and inspectable.
- Keep publication composition separate from standalone figures.
- Do not introduce a broad backend plugin registry without a demonstrated need.
- Do not reintroduce deprecated layout or postprocessing dependencies.
- Move one acceptance boundary at a time and keep release gates explicit.

## Completed foundation

### Backend-neutral orchestration

Status: complete

- Render orchestration selects explicit diagram and backend combinations.
- `RenderArtifact` represents standalone output without assuming one historical
  intermediate form.
- The runtime capability matrix is the machine-readable support authority.

### FLO-owned SVG emission

Status: complete for current public diagram families

- Swimlane emits direct SVG.
- Spaghetti emits direct SVG.
- SPPM emits direct SVG.

Remaining work in this area is renderer hardening, not backend migration.

### ELK graph layout

Status: complete for current graph-family paths

- Swimlane uses ELK with lane-aware request and normalized result contracts.
- SPPM uses ELK plus SPPM-specific row, port, boundary, and routing constraints.

Spaghetti intentionally bypasses graph layout when explicit spatial positions
are available.

### Deprecated backend removal

Status: complete for active renderer code

- No active Graphviz renderer module remains.
- No public Graphviz backend is supported.
- New renderer work targets ELK, backend-neutral geometry, and FLO-owned SVG.

Historical compatibility text may remain only when clearly labeled.

## Remaining phases

### Phase A: 0.2 renderer consolidation

Status: complete

Outcome:

- the first coherent maintained modeling-and-visualization surface
- no deprecated flowchart product surface
- consolidated SVG and ELK contracts
- deterministic artifact and documentation gates

Completed work:

1. Remove flowchart from CLI choices, capability matrix, implementation, and
   active tests in 0.2.0.
2. Preserve release-note migration guidance to swimlane and SPPM.
3. Finish shared SVG primitive extraction where more than one renderer owns the
   same presentation behavior.
4. Deepen deterministic artifact coverage for swimlane, spaghetti, and SPPM.
5. Keep strict documentation and requirements governance in CI.

Exit criteria:

- maintained renderers are SPPM, swimlane, and spaghetti
- flowchart is absent from current capability and user guidance
- identical inputs and options produce stable representative SVG artifacts
- no active renderer documentation recommends Graphviz or DOT

### Phase B: 0.3 value-stream-map delivery

Status: planned for 0.3

Outcome:

- `value_stream` is a maintained direct-SVG renderer that distinguishes
  material and information flow
- partial flow data produces explicit, deterministic diagnostics
- the renderer reuses the static-analysis and accepted renderer-platform
  primitives without reviving deprecated flowchart or Graphviz paths

Work:

1. Define a backend-neutral value-stream diagram model over canonical process,
   item, timing, queue, and approved analysis data.
2. Add ELK layout where algorithmic placement is required and emit FLO-owned
   SVG.
3. Add capability-matrix support, CLI routing, full and partial-flow fixtures,
   deterministic artifact tests, and user documentation together.
4. Promote the renderer to maintained in 0.3 and complete stable-tier gates by
   1.0.
5. Implement the accepted spaghetti partial-or-strict missing-spatial policy,
  including deterministic warnings, partial-map notices, and strict-mode
  failure.

### Phase C: publication composition

Status: planned for 0.6

Outcome:

- SPPM can produce a real page-aware publication in addition to a standalone
  SVG figure

Work:

1. Extend publication plans with figure-placement references.
2. Emit Typst source from publication plans.
3. Standardize page templates, repeated bands, captions, and continuation
   references.
4. Add stable visible step references across pages and child maps.
5. Implement deterministic warning and strict-failure behavior for readability
   constraints.
6. Verify multi-page PDFs without moving graph layout or process semantics into
   the compositor.

Accepted release ownership:

- 0.2 owns prerequisites and standalone SPPM hardening.
- 0.6 owns the complete multi-page SPPM publication acceptance boundary before
  SPPM reaches the stable renderer tier.

The normative requirement catalogs and roadmap ratify this assignment.

### Phase D: renderer stabilization

Status: planned for 0.6

Outcome:

- SPPM, swimlane, spaghetti, and value stream maps meet the stable
  renderer-tier criteria

Work:

- complete visual invariants for overlap, clipping, labels, endpoints, routing,
  and lane containment
- enforce representative golden artifacts and deterministic diagnostics
- publish input, option, artifact, and compatibility contracts
- close or explicitly waive every release-blocking renderer gap

## Diagram-family direction

### SPPM

- Continue ELK-backed direct SVG for standalone figures.
- Keep SPPM row, port, rework, and publication semantics in focused modules.
- Use Typst for composed pages rather than simulating pages inside one SVG.

### Swimlane

- Continue ELK-backed lane-aware layout and direct SVG.
- Share node, edge, label, and theme behavior with maintained process maps.
- Keep lane grouping from redefining handoff semantics.

### Spaghetti

- Continue explicit-coordinate direct SVG.
- Keep movement inference in analysis.
- Implement deterministic partial rendering by default, strict failure on
  request, and failure when no complete route remains; do not invent geometry
  or restore a deprecated layout fallback.

### Value stream map

- Build the `value_stream` renderer for 0.3 over the shared static-analysis
  foundation.
- Keep information and material flow visually and structurally distinct.
- Use explicit diagnostics for partial data instead of inventing absent flow.
- Target maintained status in 0.3 and stable status by 1.0.

### Removed Flowchart

The 0.1.x compatibility renderer was removed as part of 0.2 consolidation.
Migration guidance directs users to swimlane or SPPM.

## Validation strategy

Each active phase must preserve:

- contract unit tests
- deterministic request and result normalization
- artifact-structure tests
- representative golden drift review
- actionable diagnostics
- visual invariants proportional to renderer maturity
- strict documentation and requirement-catalog checks

## Risks

### Publication logic leaks into SVG

Mitigation:

- keep publication plans and Typst composition separate from standalone SVG
  emission

### Renderer-specific policy leaks into shared layout

Mitigation:

- keep backend-neutral contracts small and put variant semantics in focused
  adapters

### Deprecated behavior remains socially active through documentation

Mitigation:

- fail documentation governance when active examples recommend flowchart or
  active renderer notes restore Graphviz-first guidance

### SPPM absorbs every platform concern

Mitigation:

- harden swimlane and spaghetti independently and share only demonstrated
  cross-renderer primitives

## References

- `docs/design/adr/render_stack_elk_svg_typst.md`
- `docs/design/render_platform_target_architecture.md`
- `docs/design/layout_canvas_boundary_contract.md`
- `docs/design/publication_model.md`
- `docs/design/renderers/boundaries.md`
