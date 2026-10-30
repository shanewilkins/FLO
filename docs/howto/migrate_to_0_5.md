# Migrate to FLO 0.5

Package **0.5.0** introduces the breaking book-aligned source and exchange
contract. Published **0.4.3** remains the old contract; the two package versions
must not be treated as interchangeable. Source documents still declare
`spec_version: "0.1"`. Package identity, not that language marker alone,
distinguishes these producer/consumer revisions.

## Authoring changes

Use first-class fields on steps: `value_class`, measurement profiles,
`performed_by`, `uses`, `consumes`, `produces`, and `location`. Define items,
resources and locations under `process`. Move non-language annotations into
explicit `extensions`; semantic `metadata`, scalar timing, `workers` and retired
collection/endpoint aliases are rejected rather than promoted at runtime.

A duration is a supplied profile, for example:

```yaml
cycle_time:
  basis: observed
  results:
    mean: {method: mean, value: 1, unit: min}
  primary: mean
  analysis_input: mean
```

Choose the actual basis, population and statistics from your evidence. Do not
invent them during migration. `primary` selects presentation; optional
`analysis_input` independently selects modeling. Retain supporting results,
observation counts/units, cohorts, windows and provenance. Preserve measured
zero, unknown and omitted values as distinct states. Every result and parameter
must be finite portable JSON data, even when unselected.

Queue/wait references use `{ref: step_id.wait_time}` and resolve directly to a
work step's waiting profile. Full nonblank IDs, including Unicode and dots, are
preserved; references split at the final dot. References cannot chain.

Transitions use structured `handoff` and `rework` objects. An explicitly authored
empty object such as `rework: {}` denotes a relation; omission denotes none.
Boolean relation flags are rejected. Keep any supplied type, reason, frequency,
denominator, basis, note and extensions intact.

See the [normative contract](../specs/book_aligned_contract.md),
[field inventory](../specs/book_aligned_fields.md) and maintained
`examples/reference/book_washnfold.flo` fixture for complete shapes and semantics.

## Export consumers

Target and test against `flo-lang==0.5.0` when adopting this contract. Update
consumer projection models for structured relations and first-class
`value_class`; do not read retired classification metadata. Check presence with
`is not None`, not truthiness: `{}` retains its relation meaning. Consume the
supplied profiles and explicit selectors without silently replacing missing
analytical evidence with a displayed statistic.

The machine fields `cycle_time` and `changeover_time` retain their documented
processing/setup meanings. Human output uses **P/T** and **S/T**, not completion
cadence C/T or product/mode transition C/O. Numerical values and machine keys
are preserved.

## Acceptance and team boundaries

Before upgrading a consumer, validate native source fixtures, render and export
with the installed 0.5.0 wheel, then run the consumer's actual projection and
policy tests on those exports. Include empty relations, profile selectors,
Unicode waiting references and measured zero. FLO's own tests preserve these
producer contracts; they do not certify an independently maintained consumer.

The book and lss4py teams own their respective source and integration migrations.
Their acceptance remains pending until they test the target package. MPI
presentation ownership and the pinned palette comparison procedure are recorded
in [render themes](../specs/render_themes.md#mpi-palette-ownership). No peer
repository migration or new asset redistribution is performed by this release.
