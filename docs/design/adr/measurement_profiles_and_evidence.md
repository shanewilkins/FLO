# ADR: Measurement Profiles And Evidence Provenance

Status: accepted

## Context

FLO timing metadata currently stores one non-negative duration as `value` and
`unit`. That shape cannot distinguish a planned duration from an estimate,
simulation result, single observation, mean, median, percentile, or other
summary. It also cannot preserve multiple statistics calculated from one
sample, the population supporting those results, or a reference to the
authoritative evidence.

FLO is a modeling and projection system, not an event repository or general
statistical-computation package. Downstream packages such as `lss4py` may
calculate measurement profiles from event data, while authors may also supply
profiles calculated in governed worksheets or other systems. FLO needs one
contract that preserves those results without claiming to reproduce their
calculation.

Missing measurements are also semantically different from measured zero.
Parsing, canonical IR, analysis, and rendering must preserve that distinction.

## Decision

FLO will replace scalar time-duration metadata with a measurement-profile
contract before the 1.0 language and IR freeze. A belt release owns that
migration only if its accepted specification requires measurement profiles.

A profile contains:

- a required `basis` identifying whether values are `observed`, `simulated`,
  `estimated`, `planned`, or `target`;
- one or more statistic results;
- an explicit `primary` result for compact presentation;
- an optional explicit `analysis_input` result for modeled static analysis;
- shared sample context, including count, sample unit, cohort, aggregation
  level, and observation window where applicable; and
- an optional stable `evidence_ref` identifying evidence held outside FLO.

Each statistic result contains a `value`, `unit`, and `method`. A result may
also contain method parameters needed to interpret or reproduce it. The core
method vocabulary will include count, sum, minimum, maximum, mean, median,
mode, percentile, and standard deviation. Percentiles use one `percentile`
method plus an explicit percentile parameter rather than separate methods for
P90, P95, or P99. Standard deviation identifies its sample or population
convention. Methods whose definition depends on an algorithm record the
relevant parameters.

Core method identifiers are canonical lowercase strings. Extensions use a
namespaced identifier such as `lss4py:trimmed_mean`. FLO preserves supported
extension results deterministically without treating their methods as core
semantics.

The result representation will support non-scalar values where the method
requires them, such as a multimodal result. A renderer or analyzer that cannot
consume a result shape reports that limitation rather than dropping or
coercing the value.

The profile replaces the current `{value, unit}` duration contract. FLO is
pre-1.0 and will not retain a compatibility interpretation that silently gives
legacy scalar timing a statistical meaning. Migration tooling and release
notes will describe the source rewrite when the new contract is implemented.

## Evidence Boundary

An `evidence_ref` is an opaque stable reference to an external dataset,
worksheet, analysis result, or governed artifact. FLO validates and preserves
the reference but does not fetch, embed, persist, or statistically verify the
referenced evidence.

Observed event IR, imported traces, and row-level analytical data remain
separate artifacts. A producer may explicitly export a measurement profile
for use in an authored process model, but import or analysis never silently
mutates canonical designed-process IR.

Sample count is contextual evidence about the observations supporting a
profile. A `count` statistic is an analytical result and is not assumed to be
identical to sample count. Profiles with equal counts are not assumed to share
the same cohort, sample unit, window, inclusion rules, or aggregation level.

## Missingness

FLO preserves at least these states distinctly:

- a measurement field is omitted;
- a supplied field is invalid;
- a valid profile lacks a requested statistic; and
- a statistic contains a measured numeric zero.

No parser, analyzer, or renderer may replace an omitted or invalid
measurement with zero. Compact renderers may omit unavailable optional
metrics, but machine-readable projections and diagnostics retain the reason.

## Consequences

Positive consequences:

- manually authored and generated models share one measurement contract;
- FLO can render compact summaries now and richer detail later without an IR
  redesign;
- lss4py and other producers can preserve method and provenance explicitly;
- print, interactive, and machine-readable projections consume the same data;
- missing values cannot be mistaken for measured zero; and
- statistical computation remains outside FLO.

Costs:

- source, IR, schema, validation, writer, public API, renderers, static timing,
  fixtures, and documentation require a coordinated breaking migration;
- method parameters and non-scalar results require capability diagnostics;
- evidence references can be unresolved because FLO does not own the evidence
  repository; and
- profile identity and selector validation become part of the language
  contract.

## Rejected Alternatives

### Keep one scalar duration and add a statistic label

Rejected because one field cannot preserve a profile containing mean, median,
range, percentiles, count, and other results from one sample.

### Store every statistic as an independent metadata field

Rejected because sample and provenance context would be duplicated and could
silently disagree.

### Let FLO calculate profiles from event data

Rejected because event storage and statistical methodology belong in observed
data and downstream analytics layers.

### Infer average when the method is absent

Rejected because it would silently turn a declared duration into an empirical
claim.

## References

- `docs/design/adr/measurement_projection_and_analysis.md`
- `docs/design/adr/observed_branch_and_rework_frequency.md`
- `docs/design/artifact_taxonomy.md`
- `docs/policy/artifact_scope.md`
- `docs/specs/static_analysis.md`
- `docs/specs/telemetry_events.md`
