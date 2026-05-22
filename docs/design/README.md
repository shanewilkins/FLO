# FLO Design Documents

This directory holds explanatory design material for FLO.

Design documents explain architecture, implementation strategy, refactor plans,
and historical rationale. They do not override policy, specs, or schema.

## Authority Boundary

When documents disagree, use this order:

1. `schema/` for serialized structural contracts
2. `docs/policy/` for governance and source-of-truth rules
3. `docs/specs/` for normative language and diagram meaning
4. `src/flo/` for implementation that must conform to the above
5. `docs/design/` for explanatory rationale and implementation plans

If a design note appears to define normative behavior, contributors should move
or mirror the normative rule into `docs/specs/` or `docs/policy/`.

## Document Types

Common document types in this directory:

- architecture notes: broad implementation boundaries and historical decisions
- ADRs: explicit decisions with accepted or rejected options
- taxonomy notes: artifact families, ownership, and lifecycle guidance
- renderer design notes: implementation strategy for one renderer family
- migration plans: phased change plans for accepted directions
- historical notes: retained background context that is no longer authoritative

## Status Guidance

Design documents should carry a clear status near the top.

Recommended values:

- `Status: draft` for active design work not yet ratified
- `Status: proposed` for a concrete direction awaiting acceptance
- `Status: accepted` for a ratified design decision
- `Status: completed` for a delivered implementation note kept for context
- `Status: historical` for retained background material that is not current guidance

If a document has no status, contributors should treat that as a documentation
gap and add one.

## Naming Guidance

Prefer file names that reveal purpose without opening the file:

- use `*_renderer_design.md` for renderer implementation notes
- use `adr_*.md` for architecture decisions
- use `*_migration_plan.md` for phased implementation plans
- avoid near-duplicate names for overlapping topics
- avoid using `spec` in this directory unless the file is explicitly
  non-normative and says so

## Practical Lookup Guide

If you need to answer one of these questions:

- "What governs authoritative truth?" -> `docs/policy/`
- "What does this FLO artifact mean?" -> `docs/specs/`
- "How is this implemented or why was it designed this way?" -> `docs/design/`
- "What is the serialized contract?" -> `schema/`

## Render Platform Document Set

The render-platform material is intentionally split across three documents.

- `adr_render_stack_elk_svg_typst.md`
  - why the decision was made and which alternatives were accepted or rejected
- `render_platform_target_architecture.md`
  - the intended steady-state architecture and layer boundaries
- `render_platform_migration_plan.md`
  - the phased path from the current implementation to the target architecture

- `layout_canvas_boundary_contract.md`
  - one-page layout-to-canvas handoff contract and ELK/SVG ownership boundary

This split is deliberate. Keep the ADR short and decision-focused, keep the
target architecture focused on the steady state, and keep implementation phases
in the migration plan instead of duplicating them across all three files.

## Artifact Taxonomy

`artifact_taxonomy.md` is the current design-level guide to what artifact
families FLO produces, which ones are canonical versus derived, and which layer
owns each artifact family.

## Current Cleanup Notes

- `docs/design/IR.md` is retained background material and should not be treated
  as normative over `docs/specs/core_language.md`.