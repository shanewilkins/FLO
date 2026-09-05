# ADR: Observed Branch And Rework Frequency

Status: accepted

## Context

FLO currently permits free-form rework-edge metadata such as `3 per 40 cases`
and `avg 0.12 loops/case`. Those strings are useful as annotations but cannot
reliably distinguish affected work units from repeated correction occurrences,
identify the denominator, or preserve the sampling and evidence context.

Branch traversal, rework incidence, and repeated rework are different facts.
Rates calculated from incompatible cohorts or denominators must not be
silently compared or combined.

## Decision

FLO will introduce a structured observed-frequency profile for branch and
rework edges. The profile records, where applicable:

- affected work-unit count;
- traversal or correction occurrence count;
- denominator work-unit count;
- work-unit and occurrence units;
- cohort, observation window, inclusion rules, and aggregation level;
- observed, simulated, estimated, planned, or target basis; and
- an optional external `evidence_ref`.

Affected work-unit count and occurrence count remain distinct even when their
values happen to match. For example, five affected orders and eight correction
occurrences among thirty-nine eligible orders are represented as three
separate counts, not as one rate or compact string.

Rates and percentages are derived analysis results unless explicitly supplied
as statistic results with their method and denominator semantics. FLO does not
infer a missing denominator, assume one occurrence per affected work unit, or
derive a pooled rate across incompatible profiles.

Observed-frequency profiles belong to edges because they describe traversal
or return behavior. Timing profiles for correction work remain on the
correction activity and may use a different sample count. Renderers may present
the edge frequency and correction timing together, but the canonical contracts
remain separate.

Free-form explanatory notes remain available, but they are not a substitute
for the structured profile when a renderer or analyzer claims a frequency.

## Projection

A compact renderer may show a denominator-bearing form such as `5/39 orders`
and, when relevant, a repeated-occurrence form such as `8 corrections across
5 orders`. Detail and machine projections preserve all profile fields and the
evidence reference.

No renderer may display a numerator without making its denominator or explicit
lack of denominator clear when the value is presented as a rate or frequency.
Print and monochrome output retain the same meaning without relying on hover or
color.

## Analytics Boundary

FLO preserves supplied profiles and may project trace-derived profiles from an
approved telemetry-analysis result. Event repositories, row-level evidence,
cohort construction, and statistical calculation remain outside canonical
designed-process IR.

Importing or analyzing observed events does not silently attach a frequency
profile to authored process source. Promotion into a designed model requires
an explicit export or authoring action with provenance.

## Consequences

Positive consequences:

- affected work units cannot be confused with repeated occurrences;
- every displayed frequency can retain its denominator and evidence context;
- lss4py and telemetry analysis can emit one interoperable edge contract; and
- compact and detailed renderers consume the same structured meaning.

Costs:

- existing free-form `count`, `frequency`, and `rate` conventions require a
  breaking migration when the contract is implemented;
- edge validation gains profile and denominator rules; and
- profile compatibility must be checked before pooled or comparative analysis.

## Rejected Alternatives

### Keep compact frequency strings as the canonical contract

Rejected because strings are ambiguous and cannot support deterministic
analysis or alternate presentation.

### Store frequency on the correction task

Rejected because traversal belongs to the branch or rework edge, while task
timing belongs to the activity occurrence.

### Infer occurrence count from affected work-unit count

Rejected because one work unit may traverse a correction path repeatedly.

## References

- `docs/design/adr/measurement_profiles_and_evidence.md`
- `docs/design/artifact_taxonomy.md`
- `docs/policy/artifact_scope.md`
- `docs/specs/telemetry_events.md`
