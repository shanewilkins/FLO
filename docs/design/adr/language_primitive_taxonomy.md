# ADR: Language Primitive Taxonomy Direction

Status: accepted

## Context

FLO already compiles authored process descriptions into a graph-shaped IR, but
the repository has lacked one ratified answer for the author-facing primitive
hierarchy.
That gap has kept compiler, schema, fixtures, and docs work from moving into a
single implementation plan without reopening taxonomy debates.

The main unresolved questions were:

- what the umbrella flow noun should be
- whether resources should be unified conceptually
- whether rework and handoff are steps or relations
- how explicit parallel control should be introduced
- which legacy authoring aliases survive during migration

## Decision

FLO accepts a process-first primitive taxonomy with these core decisions.

1. `item` is the umbrella authored noun for what flows.
2. `material` and `information` are first-class item kinds.
3. `resource` is the umbrella concept for performers and enabling support.
4. `person` and `equipment` are first-class resource kinds.
5. `location` remains first-class.
6. `decision`, `queue`, `wait`, `subprocess`, `parallel_split`, and
   `parallel_join` are control-flow step kinds.
7. `rework` is a relation, not a step kind.
8. `handoff` is a first-class transition relation with explicit authoring in
   the first migration phase.
9. Lanes remain organizing structures rather than the deepest semantic model.
10. Generic nodes and edges remain compiled IR forms rather than the preferred
    author-facing model.

FLO also accepts the following migration surfaces.

1. Canonical process-level item authoring uses `items` with typed entries.
2. Canonical process-level resource authoring uses `resources` with typed
   entries.
3. Canonical step-level item relations are `consumes` and `produces`.
4. Canonical step-level resource relations are `performed_by` and `uses`.
5. Explicit parallel control enters first as `parallel_split` and
   `parallel_join`, without requiring higher-level sugar in the same phase.
6. Explicit handoff authoring lives on transitions or edges using `handoff` in
   the first migration phase.
7. `handoff_type` and other typed handoff categories are deferred to a
   follow-on phase.
8. Canonical surfaces should be used immediately in new docs and fixtures;
   legacy aliases are not part of the migration contract.

## Consequences

- The implementation plan can proceed without reopening primitive-hierarchy
  debates.
- The accepted migration contract is locked in
  `docs/policy/language_primitive_migration_contract.md`.
- The explanatory taxonomy note remains in
  `docs/design/language_primitive_taxonomy.md`.
- The implemented normative behavior is now described by
   `docs/specs/core_language.md`, the schema contracts, and the aligned fixture
   corpus.
- Render intent and typed metadata guidance are explicitly non-blocking for the
  first language-primitive compiler slice because their current authoritative
  structure already lives in schema.
