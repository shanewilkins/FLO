# ADR: Package Dependency Direction

Status: accepted

## Context

FLO's current package names do not consistently describe architectural role.
In particular, `flo.core` is an outer application facade and orchestration
surface, while canonical process IR and static analysis live under
`flo.compiler`. The flat `flo.render` package also mixes backend-neutral
contracts, diagram-family policy, layout integration, and SVG emission.

The existing import gates catch several forbidden top-level dependencies but do
not prevent cycles, imports of private modules across package boundaries, or
backend-specific imports from every renderer-neutral module. Adding observed
event ingestion, discovery, and conformance without a declared direction would
amplify those problems.

## Decision

FLO adopts inward dependency flow with application composition at the outside
and typed semantic models at the inside.

The target responsibilities are:

- `flo.model`: canonical process IR, constructors, and semantic validation
- `flo.observations`: observed-event IR, TraceView projection, and storage ports
- `flo.compile`: FLO source normalization into process IR
- `flo.analysis`: static, conformance, and discovery algorithms
- `flo.diagram`: backend-neutral diagram and annotation projection contracts
- `flo.render.layout`: layout ports and engine adapters
- `flo.render.svg`: SVG emission from resolved diagram geometry
- `flo.publish`: page-aware composition
- `flo.adapters`: external source and event-format parsing
- `flo.application`: CLI, public facade, use cases, and composition
- `flo.services`: outer infrastructure such as I/O, logging, and runtime
  observability

The required dependency direction is:

```text
application
  -> adapters / compile / analysis / diagram / render / publish / services

adapters -> model / observations
compile  -> model
analysis -> model / observations
diagram  -> model plus typed analysis-result contracts
render   -> diagram
publish  -> diagram assets

model and observations do not depend on application, adapters, render,
publish, services, or concrete analysis algorithms.
```

Rendering has an additional inward sequence:

```text
process and optional analysis result
  -> backend-neutral DiagramDocument
  -> LayoutRequest / LayoutResult
  -> SVG or publication asset
```

Layout and SVG code do not decide process semantics. Renderers and publishers
do not import discovery or conformance implementations.

## Current-Tree Migration

The migration is incremental rather than a flag day.

- Until renamed, `flo.core` is treated and gated as an outer application layer.
- Until moved, `flo.compiler.ir` is treated as the inner process-model layer.
- `flo.compiler.analysis` moves to the target analysis package before the
  public Python API freeze.
- New observed-event and mining code starts in the target package direction
  rather than extending the current naming debt.
- Backend-neutral render modules are explicitly registered in the architecture
  policy test until the target renderer subpackages make the boundary
  structural.
- Compatibility imports may exist only at documented public facades; internal
  packages do not depend on compatibility shims.

## CI Enforcement

CI must enforce:

- no dependency cycles between sibling packages, recursively through the
  maintained package depth
- declared forbidden dependencies for inner process and observed-event models
- no direct import of another top-level FLO package's private module
- no SVG or diagram-family-specific imports from registered backend-neutral
  renderer modules
- public import and clean installed-wheel smoke tests
- one maintained import-policy source; stale parallel checkers are removed

New target packages receive import contracts in the same change that introduces
them. A package move is not complete until its old path is removed or retained
only as an explicit compatibility facade and the gates pass without broad
ignore rules.

## Consequences

Positive consequences:

- CI failures describe violations of an accepted dependency direction
- event ingestion and mining do not leak into process-model or renderer code
- package names can be cleaned incrementally without accepting new debt
- private implementation paths stop becoming accidental integration APIs

Costs:

- several pre-1.0 package moves and import migrations are required
- renderer-neutral modules require explicit registration during migration
- clean wheel smoke tests add CI time

## Rejected Alternatives

### Gate only the current top-level package graph

Rejected because it would preserve misleading ownership and would not protect
the internal renderer or future observed-event boundaries.

### Complete a flag-day package rewrite before adding gates

Rejected because the ungated rewrite would be difficult to review and could
allow new cycles or private imports during migration.

### Keep architecture checks in a standalone AST script

Rejected because the existing script is stale and duplicates the enforced
Import Linter configuration. Narrow source-shape checks remain appropriate only
where Import Linter cannot express the transitional boundary clearly.

## References

- `pyproject.toml`
- `.pre-commit-config.yaml`
- `docs/design/render_platform_target_architecture.md`
- `docs/design/renderers/boundaries.md`
- `docs/design/adr/observed_event_mining.md`
