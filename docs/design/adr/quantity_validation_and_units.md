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

Pint owns spatial, duration, and measured-quantity conversion through
`flo.process.units`. FLO retains the supported-unit vocabulary. One lazily
initialized registry serves these consumers;
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
dependencies and registry initialization on the first conversion.
This assessment does not claim a measured performance improvement.

## Duration integration

After common diagnostic delivery, the duration migration uses that same lazy
registry. The boundary explicitly maps FLO's `s`, `m`, `min`, `hr`, and `d` to
Pint time units. Duration `m` means minutes; spatial `m` remains metres.
Pint's additional unit names, expressions, and dimensions do not become
accepted FLO duration syntax.

The conversion inventory and ownership are:

| Surface | Responsibility after migration |
| --- | --- |
| `flo.process.units` | Duration allowlist, explicit aliases, and Pint conversion through the existing registry. |
| `flo.process.durations` | Finite nonnegative scalar checks and normalization to seconds; the handwritten seconds-per-unit table is removed. |
| IR validation and timing analysis | Retain existing validation codes, timing states, and analysis arithmetic while consuming the shared normalization boundary. |
| SPPM timing metadata and publication footer | Use shared conversions for minute labels; retain authored processing/setup labels and footer unit-selection policy. |
| Inspect text and value-stream SVG | Use shared conversions while retaining their existing seconds/minutes/hours selection and formatting. |

The canonical `{value, unit}` records, measurement identity/references, omissions,
and authored numeric types are not rewritten. Explicit zero remains measured.
Invalid or non-finite values, including conversion overflow, follow the existing
source-aware error or analysis-diagnostic paths rather than being treated as
missing data or leaking library exceptions. This duration change alone does not
alter resource quantity validation.

Compatibility fixtures cover every supported source/target duration unit,
the minute/metre distinction, case/whitespace handling at the existing scalar
boundary, rejected library-only units, zeros, overflow, authored exchange,
CLI/API reports, display policy, and lazy/shared registry use. Existing timing,
diagnostic-delivery, and SPPM artifact baselines remain verification gates.

## Measured resource quantity integration

The canonical-equivalence policy was selected on 2026-10-25: a measured
quantity's optional `canonical_value` and `canonical_unit` must describe the
same amount as its authored `value` and `unit`, not merely a compatible
dimension. The comparison uses relative tolerance `1e-9` and absolute
tolerance `0`, measured against the larger absolute amount. Tiny positive
quantities do not acquire a fixed absolute-error allowance.

The supported measure vocabulary remains `mg`, `g`, `kg`, `ml`, `l`, `mm`, `cm`,
and `m`. Pint converts only within a dimension through the existing registry.
No new FLO syntax, unit expressions, or Pint objects enter source or JSON.
Measured/spatial `m` means metres; duration `m` remains minutes.

This is an intentional validation-semantics tightening, not a syntax change:

- `250 g` with canonical `0.25 kg` is valid and remains authored that way.
- `250 g` with canonical `99 kg` fails with `E1223`.
- `250 g` with canonical `0.25 l` fails with `E1222`; no material density or
  mass-to-volume conversion is inferred.
- A canonical conversion that overflows or underflows to zero fails with
  `E1224` rather than being compared as infinity or zero.
- Omitting both canonical fields remains valid; validation does not synthesize
  them or rewrite either pair. Existing malformed-value and unit codes remain.
- Count quantities retain integer `value >= 1`, optional `unit: each`, and
  qualifiers. Measured values remain finite and strictly positive, unlike
  durations where zero is a valid observation.

The same checks apply to items, resources, locations with quantities, and
legacy material/equipment/worker collections, including nested groups.
New failures carry the authored quantity field path, excerpt, repair guidance,
and validation exit code 4 through the common CLI/API report. The normative
contract is in [Core Language](../../specs/core_language.md).

Consumers retain authored evidence: canonical JSON preserves both quantity
pairs, and ingredient/resource text continues to display the authored amount.
Schemas keep the existing shapes; cross-field dimensional/equivalence checks
are semantic validation, like reference and graph rules.

## Remaining boundaries

The next source-model design should preserve explicit `{value, unit}` exchange
records and authored units. Pydantic should replace handwritten shape and field
checks. Pint should perform dimensional compatibility checks and conversions
inside measured-quantity consumers. No Pint objects or library-specific strings
should become the JSON interchange contract.

Keep dimension and process meaning separate: processing and waiting durations
share a time dimension but have different roles; worker and material counts
retain entity meaning even when physically dimensionless. Continue explicit
reference, graph, timing-state, and measurement-provenance validation.

The duration boundary maps FLO's `m` alias explicitly to minutes; measured and
spatial `m` mean metres. Canonical measured quantities use the equivalence
policy above. Mass-to-volume conversion would require a separate accepted
material-information contract and is not implemented.

Source shape validation and duration conversion preserve existing language
behavior. Measured quantities add the explicit semantic checks above without
changing syntax. Internal geometry and analysis dataclasses remain appropriate;
a general Pydantic/Pint wrapper framework is not needed. Any later migration must delete superseded validation/conversion
code and preserve source-aware diagnostics and schema conformance.
