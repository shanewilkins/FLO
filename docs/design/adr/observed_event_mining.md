# ADR: Observed Events, Discovery, And Conformance

Status: accepted

Implementation boundary refined by: `simplified_package_architecture.md`

## Context

FLO needs to ingest CSV, XES, and OCEL 2 event logs, compare observed behavior
with authored process models, discover candidate process structure, identify
observed trace variants, and render or analyze resulting process structures.

The existing canonical process IR represents designed process meaning. The
accepted telemetry boundary already requires imported observations to remain
separate from authored source and canonical designed-process IR. OCEL 2 also
contains object-centric relationships that cannot be represented faithfully by
the existing case-oriented `flo_trace` envelope.

The architecture therefore needs to support both:

- process discovery, which derives candidate structure from observations
- process conformance, which compares observations with an exact reference
  process and may identify candidate variants

## Decision

FLO will use two distinct semantic IR families.

1. `ProcessIR` represents process structure. Authored, discovered, and
   conformance-derived candidate structures use the same validated process IR.
2. `ObservedEventIR` represents observed events, objects, types, attributes,
   temporal object changes, qualified event-to-object relationships, and
   object-to-object relationships.

The existing case-oriented `flo_trace` contract remains a derived `TraceView`
of `ObservedEventIR`. It does not become the universal observed-event model.
Projection requires explicit, recorded parameters and never silently flattens
object-centric relationships.

## Ingestion Boundary

CSV, XES, and OCEL 2 parsers are replaceable inbound adapters. They normalize
into `ObservedEventIR` through typed ports. Downstream projection, alignment,
conformance, and discovery code does not depend on parser-specific types.

The staged delivery is:

- 0.7: CSV, XES, and OCEL 2 JSON
- 0.8: OCEL 2 XML and SQLite through the same port

CSV uses an explicit or recorded mapping profile. XES uses a documented
semantic profile. FLO does not guess ambiguous columns, classifiers, identity,
timezone, lifecycle, or projection rules.

The parser boundary is local-first, deterministic, resource-bounded, and safe
for untrusted tabular, JSON, XML, and SQLite input. XML external entities and
network resolution are prohibited. Heavy dataframe or process-mining packages
are not core runtime dependencies; advanced implementations may use a later
optional mining dependency group behind the same typed contracts.

Importers expose a streaming/store-oriented port. The initial implementation
may use a bounded in-memory store, but analysis APIs do not assume that an
entire future dataset must fit in memory. A SQLite-backed store may be added
without changing semantic contracts.

## Discovery

Discovery consumes validated `ObservedEventIR` or an explicit `TraceView` and
emits a typed result envelope containing one or more immutable candidate
`ProcessIR` values, provenance, algorithm identity and version, parameters,
projection choices, evidence or confidence, limitations, and diagnostics.

A discovered model is not authored process truth. FLO requires an explicit
accept or export operation before candidate process IR can become `.flo` source
or a declared process-family variant.

Renderers and ordinary model analyzers consume the candidate `ProcessIR`; they
do not import discovery algorithms or input adapters.

## Conformance

Conformance consumes an immutable exact `ProcessIR` plus immutable
`ObservedEventIR` or an explicit `TraceView`. It emits a typed
`ConformanceResult` containing aligned evidence, deviations, measures, stable
model and event references, unresolved evidence, and optional candidate
variant `ProcessIR` values.

Conformance never mutates the reference process or observed dataset. A
renderer-neutral diagram projection may combine process structure with a
conformance result to produce overlays. Renderer implementations do not import
conformance algorithms.

## Variant Terminology

FLO keeps these concepts distinct:

- a trace variant is a distinct observed activity sequence or explicitly
  defined object-centric observational pattern
- a candidate structural variant is inferred process structure that has not
  been accepted as source truth
- a declared process variant is an authored member of an accepted process
  family

Candidate promotion is explicit and preserves provenance. Conformance or
discovery never silently creates or edits declared process-family source.

## Reproducibility

Discovery and conformance results record input identities, projection choices,
configuration, algorithm version, FLO version, and a random seed when
applicable. Deterministic methods use stable ordering and tie-breaking.
Stochastic methods require an explicit or recorded seed. Nondeterminism is not
hidden behind an apparently canonical artifact.

## Consequences

Positive consequences:

- one process IR remains usable by renderers and model-analysis packages
- object-centric input is preserved without contaminating designed-process IR
- format adapters, mining algorithms, and renderers remain replaceable
- inferred structure is auditable and cannot silently become source truth
- large-log storage can evolve without replacing semantic contracts

Costs:

- FLO owns an additional typed observed-event model and projection boundary
- conformance overlays require a renderer-neutral annotation projection
- candidate acceptance and provenance become explicit workflow concepts
- object-centric-native mining remains separate from initial case-projected
  algorithms

## Rejected Alternatives

### Put imported events in canonical process IR

Rejected because observed executions are evidence, not designed process truth,
and because it would couple every renderer and static analyzer to event data.

### Flatten OCEL into cases during import

Rejected because there may be no single correct case notion and flattening can
discard qualified relationships, object history, and multi-object context.

### Give discovery a renderer-specific graph format

Rejected because discovered structure should be reusable by validation,
rendering, static analysis, comparison, and source export.

### Promote inferred variants automatically

Rejected because evidence-derived candidates require human review and explicit
acceptance before becoming authored process truth.

## References

- `docs/specs/telemetry_events.md`
- `docs/policy/telemetry_privacy.md`
- `docs/design/artifact_taxonomy.md`
- `docs/design/adr/process_variants.md`
- `docs/requirements/user_requirements.csv`
- `docs/requirements/technical_requirements.csv`
