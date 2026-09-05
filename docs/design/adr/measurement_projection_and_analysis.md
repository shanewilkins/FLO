# ADR: Measurement Projection And Analysis Selection

Status: accepted

## Context

A measurement profile may contain several statistics, while a compact process
box has room for only a small selection. Detailed interactive or publication
views may show the complete profile, and machine-readable output must preserve
it losslessly.

Static timing analysis has a different responsibility. It describes modeled
timing over the authored graph and already refuses unsupported incomplete,
cyclic, rework, and parallel cases. It must not become a statistical engine or
silently choose a descriptive statistic merely because one is available.

## Decision

FLO will support three measurement projection classes:

- `compact` shows the profile's explicit primary result and approved sample
  context that fits the diagram;
- `detail` shows all supported results, method parameters, sample context,
  basis, and evidence identity; and
- `machine` preserves the complete profile without presentation loss.

The profile's `primary` selector controls compact presentation. FLO does not
choose mean, median, or another method through an implicit preference order.
An unavailable or unsupported primary result produces an actionable
diagnostic and never falls back silently to another result.

Detail is a semantic projection, not an interaction mechanism. Standalone SVG,
interactive hosts, and composed publications may expose it differently. A
clickable node may open detail in a capable host, while print and PDF output
must provide an equivalent table, callout, appendix, or companion artifact.
No required meaning may depend on hover, clicking, scripting, or color alone.

## Static Timing Selection

Modeled static timing consumes a profile only when `analysis_input` explicitly
selects one numeric, dimensionally compatible statistic result. It never uses
the compact `primary` result merely because that result is visible.

The static analyzer:

- preserves the selected method, basis, unit, and profile reference in its
  typed result;
- applies the existing completeness, branching, rework, cycle, and parallel
  refusal rules;
- labels arithmetic over selected node results as modeled timing; and
- reports an unavailable analysis input when selection is missing, invalid,
  non-scalar, or dimensionally incompatible.

The static analyzer does not:

- calculate descriptive statistics;
- validate or retrieve external evidence;
- select a method implicitly;
- combine non-selected profile results; or
- label a sum of node means, medians, minima, maxima, or percentiles as the
  corresponding empirical end-to-end statistic.

An explicit selection authorizes use as a modeled scalar. It does not assert
that node cohorts are compatible or convert the result into an observed
order-level measure. Empirical end-to-end statistics must be calculated from
complete work-unit evidence outside static graph analysis.

## Renderer Contract

Renderer-neutral diagram models will carry stable references to projected
measurement content rather than flattening the complete profile into label
strings. Renderers declare which projection classes and result shapes they
support. Unsupported detail produces deterministic diagnostics.

Compact timing labels identify the selected method when the value has a
statistical method, for example `Avg CT`, `Median WT`, or `P90 C/O`. A bare
`CT`, `WT`, or `C/O` label must not imply a mean. Sample count may be shown
with the compact result. Shared captions may deduplicate sample context only
when cohort, sample unit, window, inclusion rules, aggregation level, and
other governed sample identity all match.

## Consequences

Positive consequences:

- compact diagrams remain readable without discarding detailed evidence;
- future interactive inspection does not require a canonical-data redesign;
- book and print output remains complete without browser behavior;
- display choice and modeled-analysis choice cannot be conflated; and
- renderers do not implement statistical arithmetic.

Costs:

- render capability contracts gain measurement projection declarations;
- detailed publication placement needs layout and composition work; and
- analyzers and renderers must diagnose unsupported selected result shapes.

## Rejected Alternatives

### Use the primary display statistic for static analysis

Rejected because presentation priority does not establish mathematical or
process-model suitability.

### Prefer average automatically

Rejected because it invents a policy and can misrepresent planned, simulated,
or non-mean profiles.

### Make detail available only through clickable SVG

Rejected because publication artifacts must remain usable in print, PDF, and
non-scripted environments.

## References

- `docs/design/adr/measurement_profiles_and_evidence.md`
- `docs/design/publication_model.md`
- `docs/design/render_platform_target_architecture.md`
- `docs/specs/sppm.md`
- `docs/specs/static_analysis.md`
