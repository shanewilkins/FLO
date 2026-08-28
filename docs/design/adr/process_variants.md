# ADR: First-Class Process Families And Variants

Status: proposed

## Context

FLO currently compiles one authored process description into one canonical,
graph-shaped process model. It supports runtime branching through decisions,
source composition through includes, process revisions through intended process
versioning, and multiple visual projections through render views.

Those capabilities do not make related process definitions first-class. Real
process portfolios commonly contain site-specific, product-specific,
service-level, regulatory, and as-is/to-be variants that should share stable
lineage without being represented as runtime branches or unrelated copies.

Ordinary includes are intentionally additive. Included step lists are appended,
duplicate step IDs are rejected, and include order is not an inheritance or
override mechanism. Retaining that behavior protects readable and deterministic
composition.

Process-version preservation is also a prerequisite. The canonical schema
allows `process.version`, but the current compiler projection drops an authored
version. Variant identity must not be built on that incomplete identity path.

## Proposed Decision

FLO should introduce process families as an authoring and resolution layer.

- A process family groups multiple explicitly declared concrete variants.
- Every variant has stable family, variant, concrete process, and version
  identity.
- Variant selection and composition complete before canonical compilation and
  semantic validation.
- A resolved variant is one ordinary canonical FLO process. Canonical nodes and
  edges never contain unresolved variant conditions or sets of alternatives.
- Existing renderers, analyzers, exporters, telemetry alignment, and
  publication consume the resolved canonical process without inventing
  variant-specific graph semantics.

The initial authoring contract should use a process-family manifest that
enumerates concrete variant entry files. Those entry files may reuse ordinary
FLO includes for shared fragments. The first contract should not include a
general inheritance, templating, parameter-substitution, or arbitrary merge
language.

## Proposed Identity Semantics

- `family_id` identifies the broader business process family.
- `variant_id` identifies one stable configuration or scenario within the
  family.
- `process.id` identifies the exact concrete designed process used by canonical
  artifacts and telemetry alignment.
- `process.version` identifies a historical revision of that concrete process.
- Variant dimensions such as site, product, region, or service level are
  descriptive and filterable. They do not implicitly generate variants or
  define identity.
- `spec_version` continues to identify FLO language syntax and is unrelated to
  process version.

Shared activities should retain the same step ID across variants only when they
retain the same process meaning. FLO comparison and telemetry alignment must
use stable IDs rather than names, source positions, or approximate matching.

## Proposed User Operations

FLO should support deterministic operations to:

- list variants in a family
- select one exact variant
- use an explicitly declared default variant
- inspect, validate, render, analyze, export, or publish one variant
- run supported operations for all variants with stable ordering and
  per-variant diagnostics
- compare two variants by stable identities

Omitting selection should succeed only when the family contains one variant or
declares an explicit default. Ambiguity must fail rather than silently choosing
a source-order or filename-based default.

## Initially Excluded

The first process-family contract should exclude:

- last-definition-wins step replacement
- arbitrary YAML merge behavior
- condition expressions embedded in canonical steps or transitions
- automatic Cartesian products of dimension values
- variant inference from filenames or directory layout
- parameter substitution in identifiers or process content
- general-purpose templating or scripting

If representative process-family corpora demonstrate that shared fragments are
insufficient, a later decision may add a small typed `add`, `replace`, and
`remove` change-set contract. Such operations would require exact ID targeting,
conflict detection, deterministic application, and an inspectable resolved
result.

## Open Decisions

Before acceptance, this ADR must resolve:

1. The process-family manifest filename convention and serialized schema.
2. The exact source and canonical IR shape for family, variant, version, and
   dimension fields.
3. Whether the family contract requires the next FLO `spec_version`.
4. CLI command names, selector syntax, default behavior, and all-variant failure
   policy.
5. Public Python API request and result types.
6. Artifact naming and provenance requirements.
7. The normalized variant-comparison report schema.
8. Whether family-level telemetry aggregation is part of the initial feature or
   a later analysis surface.

## Alternatives

### Treat variants as decision branches

Rejected as the general model. A decision describes runtime control flow within
one concrete process; it does not identify a site, product, policy, or scenario
as an independently versioned process definition.

### Use includes as implicit inheritance

Rejected. Silent override-by-order would weaken existing duplicate-ID safety
and make the resolved model harder to review and reproduce.

### Store lineage only in free-form metadata

Rejected as the target. Metadata can support an interim convention, but
first-class enumeration, selection, diagnostics, interchange, and compatibility
need a governed structural contract.

### Put unresolved variability in canonical IR

Rejected. It would force every renderer, analyzer, exporter, and telemetry path
to reinterpret the same variability and would undermine FLO's single canonical
process meaning.

## Consequences

Positive consequences:

- related process definitions gain stable, inspectable lineage
- existing downstream process consumers retain a simple one-process contract
- shared fragments reduce duplication without hidden mutation
- deterministic comparison and exact telemetry alignment become possible
- as-is/to-be and local/global reviews no longer rely on unrelated file copies

Costs and risks:

- FLO gains a second source artifact kind and a resolver lifecycle
- CLI, public API, writer, formatter, source schema, migration, sharing, and
  telemetry contracts all require coordinated updates
- artifact naming and batch failure behavior require careful compatibility
  design
- process-version propagation must be fixed first

## Requirements Affected

New proposed user requirements: `UR-065` through `UR-069`.

New proposed technical requirements: `TR-091` through `TR-094`.

Existing requirements amended for cross-cutting compatibility: `UR-008`,
`UR-042`, `UR-045`, `UR-053`, `UR-055`, `UR-056`, `UR-058`, `UR-060`,
`UR-061`, `TR-012`, `TR-067`, `TR-069`, `TR-079`, `TR-080`, `TR-081`,
`TR-083`, `TR-085`, and `TR-086`.

## Release Posture

The identity, resolution, CLI, public API, and source-writer contract should be
resolved before the 0.7 language and IR freeze candidate. Source-schema,
editor, migration, and comparison hardening may complete in 0.8. Accepted
variant behavior must meet the 1.0 compatibility and determinism gates.
