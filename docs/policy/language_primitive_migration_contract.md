# FLO Language Primitive Migration Contract

Purpose: lock the decision boundaries required before the language-primitive
implementation begins across compiler, schema, fixtures, renderers, and docs.

This policy freezes the accepted migration contract for the next source-model
evolution.
It does not claim that every accepted behavior is already implemented.
Current implemented normative semantics remain governed by
`docs/specs/core_language.md` until implementation, schema, tests, and specs
are updated together.

## Core Rule

For this migration, the implementation plan must not reopen primitive-hierarchy,
canonical-source-surface, or compatibility-posture debates.
Those decisions are locked here so Phase 1 can proceed without further design
drift.

## Accepted Primitive Direction

The accepted primitive hierarchy is:

- `item` as the umbrella authored noun for the thing that flows
- `material` and `information` as first-class item kinds
- `resource` as the umbrella concept for performers and enabling support
- `person` and `equipment` as first-class resource kinds
- `location` as first-class
- `decision`, `queue`, `wait`, `subprocess`, `parallel_split`, and
  `parallel_join` as control-flow step kinds
- `rework` as a relation, not a step kind
- `handoff` as a first-class transition relation with explicit authoring in
  this migration phase
- lanes as organizing structures rather than the deepest semantic model
- generic nodes and edges as compiled IR forms rather than the primary
  author-facing model

## Canonical Source Surfaces

The canonical authored surfaces for this migration are locked as follows.

### Process-level items

- Canonical surface: top-level `items` collection.
- Each authored item entry should identify its kind as `material` or
  `information`.
- `materials` and `information` are not part of the canonical source surface
  for this migration and should not be used in new docs or fixtures.

### Process-level resources

- Canonical surface: top-level `resources` collection.
- Each authored resource entry should identify its kind as `person` or
  `equipment`.
- `locations` remains a separate first-class collection rather than becoming a
  resource subtype.
- `workers` and top-level `equipment` are not part of the canonical source
  surface for this migration and should not be used in new docs or fixtures.

### Step-level item relations

- Canonical surfaces: `consumes` and `produces`.
- `inputs` and `outputs` are not part of the canonical source surface for this
  migration and should not be used in new docs or fixtures.

### Step-level resource relations

- Canonical surfaces: `performed_by` and `uses`.
- Step-level `workers` and `equipment` are not part of the canonical source
  surface for this migration and should not be used in new docs or fixtures.

## Parallel And Handoff Decisions

### Parallel control

- Phase 1 introduces `parallel_split` and `parallel_join` as explicit step
  kinds.
- No higher-level parallel sugar is required in the same phase.

### Handoff authoring

- Explicit handoff declarations live on transitions or edges.
- Canonical explicit key for this migration phase is `handoff`.
- Typed handoff categories are deferred and may be introduced in a follow-on
  phase.
- An edge may be both handoff-bearing and rework-bearing.

## Compatibility Posture

- New examples, normative docs, and user-facing docs should use canonical
  surfaces immediately.
- Fixtures should be authored in canonical form immediately.
- Legacy aliases are not part of the migration contract and are not guaranteed
  compatibility surfaces.
- Temporary parser shims may exist as implementation details during rollout,
  but they should not be documented as normative authoring surfaces.

## Non-Blocking Deferrals

The following topics do not block the language-primitive implementation plan.

### Typed metadata guidance

- `schema/flo_types.json` is the authoritative contract for typed metadata.
- `docs/design/typed_metadata.md` is an explanatory guide and does not need to
  become a policy or spec blocker before compiler work begins.

### Render intent source metadata

- `schema/flo_ir.json` is the authoritative structural contract for
  `process.metadata.render`.
- `docs/design/render_intent_schema.md` may continue to document rollout and
  authoring guidance without blocking the language-primitive migration.

## Required Cross-References

- Decision record: `docs/design/adr/language_primitive_taxonomy.md`
- Explanatory taxonomy note: `docs/design/language_primitive_taxonomy.md`
- Active execution plan: `notes/language_primitive_taxonomy_implementation_plan.md`