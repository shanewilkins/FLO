# ADR: FLO-owned layout finalization and SVG consumption

Status: accepted

Refines: `render_stack_elk_svg_typst.md` and
`../render_platform_target_architecture.md`.

## Context

The accepted split between diagram semantics, layout, SVG emission, and document
composition remains appropriate. Its statement that ELK owns placement and
routing was too absolute for FLO's explicit width wrapping, correction-row rules,
shape attachments, and annotation avoidance. These are legitimate FLO rules;
implementing them inside SVG assembly makes layout results incomplete and their
ownership difficult to enforce. The architecture validation found that golden
generation can also duplicate the production sequence even while bytes agree.

## Decision

FLO retains ELK as an algorithmic layout engine and its four substantive packages.
No engine replacement, browser runtime, new top-level package, or general layout
plugin framework is introduced by this decision.

1. A diagram renderer owns its projection, measurements, semantic routing policy,
   wrapping, and annotation conventions. SPPM-specific correction placement and
   spacing belong to SPPM-owned layout policy, not a nominally neutral ELK adapter.
2. Renderer-neutral layout infrastructure owns engine protocol/execution,
   coordinate normalization, shared contracts, and genuinely reusable geometry
   mechanisms. It may execute injected diagram policy; it does not define it.
3. One production rendering orchestration path owns the order of geometry
   preparation, projection/measurement, engine execution, diagram finalization,
   viewport resolution, and emission. CLI and direct Python rendering use it;
   golden and diagnostic tools must consume it with explicit resolved options.
   Tooling may observe stage inputs/results, not assemble a competing sequence.
4. Before shape emission, FLO produces an inspectable finalized geometry value
   containing node and visible-lane bounds, routed edges and shape attachments,
   label/callout/token placements, occupied bounds, and diagnostics. Artifact
   viewport, fit, and scale remain explicit in the rendering result. Engine output
   is an intermediate value, not this final contract.
5. SVG shape emission consumes that finalized geometry. It may format coordinates,
   serialize paths/text, and apply paint and typography tokens. It must not choose
   placement, reroute edges, clip attachments, infer correction membership, or
   run collision-avoidance policy. Painting a supplied viewport transform is
   distinct from deciding diagram layout.
6. Publication planning remains adjacent to standalone figure rendering. Typst
   composes pages and references figures; it does not place or route process nodes.
   Headers/footers on standalone SVGs do not imply full paginated acceptance.

The finalized value's exact name and module layout are implementation choices
for the bounded remediation slices. It must expose what SVG emission actually
uses, preserve source IR, and support deterministic stage inspection without a
second rendering implementation. Explicit supported precomputed-layout entrypoints
must identify their stage and cannot masquerade as complete artifact rendering.

## Effective obligations and migration

This clarification is effective for acceptance of the next release under TR-118.
It preserves the existing responsibility split rather than granting permission
for scattered repairs. R1 implements shared execution and R2 restores diagram
policy ownership, closing AF-003 and AF-002. R3a implements the routed-geometry
stage before SVG. R3b completes attachments/annotations and closes AF-001.
Clean-candidate acceptance remains required in [the validation report](../architecture_validation.md).

Migration must preserve semantic identities, graph meaning, diagnostics, and
reviewed public output. A stage should move with its tests and ownership checks;
file extraction alone does not close a finding. Keep independent final-SVG checks
alongside finalized-geometry checks. No new source language or public CLI options
are required to implement this decision.

A browser may be used as a test consumer for font/legibility acceptance, consistent
with existing CI. The accepted no-browser-runtime constraint continues to prohibit
making product rendering depend on a browser.
