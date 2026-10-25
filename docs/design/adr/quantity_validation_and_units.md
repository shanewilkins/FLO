# ADR: Quantity Validation And Units

Status: accepted

## Context

The initial Pydantic configuration change added a typed model tree ahead of
existing flattening and numeric validation. It increased duplication. Separately,
movement analysis could calculate distances only for identical spatial units,
while spaghetti rendering projected raw mixed-unit coordinates as though their
scales matched. A scoped Pint trial can resolve that inconsistency without
redesigning source models or exchange formats.

## Decision

Configuration uses one Pydantic model at the existing application validation
boundary. A declarative TOML mapping replaces the procedural flatteners. Values
are validated after preset selection and CLI overrides; consumed containers must
still be tables. Integer strings and whole-number floats are accepted; booleans,
fractional integer values, and non-finite dimensions are rejected. Existing
option aliases, precedence, omission, and theme ownership remain intact.

Pint owns spatial conversion through `flo.process.units`. FLO retains the
supported-unit vocabulary. One lazily initialized registry serves the trial;
ordinary application import does not import Pint or create a registry.

The shared derived location index converts mixed supported units to metres.
Both movement inference and SVG projection consume that index. Homogeneous maps
retain their existing scale, and canonical quantities are never rewritten.
The contract is specified in [Spaghetti Map](../../specs/spaghetti_map.md).

## Trial assessment

Keep the spatial trial: it replaces the identical-unit limitation and produces
identical SVG for equivalent mixed-unit and metre coordinates. Tests cover both
movement channels, nonzero endpoints, all supported conversions, reverse routes,
input immutability, unsupported units, invalid numeric evidence, and overflow.
The cost is one runtime dependency plus its `flexcache` and `flexparser`
dependencies and registry initialization on the first mixed-unit conversion.
This assessment does not claim a measured performance improvement.

## Direction for later source models

The next source-model design should preserve explicit `{value, unit}` exchange
records and authored units. Pydantic should replace handwritten shape and field
checks. Pint should perform dimensional compatibility checks and conversions
inside measured-quantity consumers. No Pint objects or library-specific strings
should become the JSON interchange contract.

Keep dimension and process meaning separate: processing and waiting durations
share a time dimension but have different roles; worker and material counts
retain entity meaning even when physically dimensionless. Continue explicit
reference, graph, timing-state, and measurement-provenance validation.

Before migrating durations, map FLO's `m` duration alias explicitly to minutes;
spatial `m` means metres. Before migrating measured resources, define whether a
canonical value must be dimensionally compatible only or numerically equivalent
within an explicit tolerance. Mass-to-volume conversion requires authored
material information and must not be inferred from unit names.

These source/duration/resource migrations are follow-up designs, not implemented
or newly accepted language behavior. Internal geometry and analysis dataclasses
remain appropriate; a general Pydantic/Pint wrapper framework is not needed for
this trial. Any later migration must delete superseded validation/conversion
code and preserve source-aware diagnostics and schema conformance.
