# ADR: Canonical IR Metadata And Subprocess Hierarchy

Status: accepted

## Context

FLO must preserve authored business context without turning every descriptive
key or renderer option into core process semantics. The previous canonical IR
shape mixed three different concerns inside `process_metadata`: referenced
process entities, FLO-understood extension contracts, and arbitrary annotations.
That made it difficult for analytics and downstream integrations to distinguish
stable process meaning from pass-through data.

Subprocess containment also had an inconsistent status. The compiler and
validator understood `subprocess_parent`, but earlier roadmap language could be
read as deferring hierarchy itself alongside future child-map and inline
publication features.

## Decision

FLO uses three data tiers.

1. **Canonical semantics** are explicit typed IR fields when they participate
   in process identity, references, semantic validation, static analysis, or a
   public interchange promise. This tier includes process identity and version,
   owner, business units, lanes, nodes, edges, items, resources, locations, and
   subprocess membership.
2. **Typed extensions** have FLO-owned schemas and validation but do not define
   process execution or control-flow meaning. Render intent and publication
   settings are the current example. A typed extension may retain a compatible
   serialized location under `process.metadata` while exposing a typed internal
   contract.
3. **Opaque annotations** are losslessly preserved under `metadata`, but FLO
   does not infer process semantics from them. Promotion into either typed tier
   requires an explicit specification and compatibility decision.

A field does not become canonical merely because one renderer consumes it.
Promotion requires stable identity, cross-object reference, semantic
validation, analysis, or an explicit public compatibility promise.

The canonical subprocess representation is a flat node collection with an
optional single `subprocess_parent` reference on a child node. The serialized
hierarchy is a current IR promise:

- the parent must resolve to a node whose kind is `subprocess`;
- containment is acyclic and may be nested;
- containment does not itself create control-flow edges;
- hierarchy preservation does not promise entry, exit, execution, pagination,
  or expansion behavior; and
- top-level, child-map, bounded-inline, continuation, and pagination behavior
  belongs to the `0.4` renderer-stabilization milestone.

## Implementation Boundary

Process owner, business units, lanes, items, resources, and locations are
explicit IR fields. `subprocess_parent` is an explicit `Node` field, and render
intent is an explicit typed-extension field. Compatibility normalization at
the IR boundary promotes legacy in-memory metadata and attribute-map values
once, removes the shadow copies, and preserves accepted source and serialized
field names. Current validation checks missing parents, wrong parent kinds,
self-parenting, and cycles.

## Consequences

- Static analytics can depend on typed domain collections rather than inspect
  arbitrary mappings.
- Renderer and publication configuration remains portable without becoming
  process control-flow meaning.
- Unknown metadata can round-trip without acquiring accidental semantics.
- Serialized hierarchy can be consumed now, independently of richer `0.4`
  subprocess presentation.
- Adding a new first-class field requires schema, compiler, round-trip, and
  compatibility evidence; adding an opaque annotation does not.
