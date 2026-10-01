# FLO recommendations from the White Belt mapping revision

Date: 2026-09-04
Status: proposal for the FLO team; not an implemented FLO contract

## Why this matters

The Modern Process Improvement book is refactoring Chapters 7–9 around an
event log as the foundational evidence. The process worksheet is an aggregated
projection of that evidence, and the SPPM is a selective visual projection of
the worksheet. The analytics readout answers process-performance questions.
Learners perform the calculations on paper; Yellow Belt later introduces
automation with lss4py.

White Belt will teach count, sum, minimum, maximum, median, mean, mode, simple
percentages, and P90. Standard deviation, coefficient of variation, and formal
inference remain outside this arc. Teaching a statistic does not imply that
every process box should display it.

## Separate evidence, summaries, and presentation

| Artifact | Responsibility |
| --- | --- |
| Event log | Preserve work-unit identity, activity occurrence, timestamps, context, variants, and rework evidence. |
| Map worksheet | Group comparable observations by activity; record role, value class, sample count, timing summaries, and evidence references. |
| SPPM | Show sequence, ownership, queues, split/rejoin behavior, and correction paths with selected timing summaries. |
| Analytics readout | Report order/cohort measures: lead-time summaries, promise failures, PCE, throughput, WIP, and Little's Law under explicit boundaries. |

FLO should consume summaries and their provenance. It need not become an
event-log storage or statistical-computation system.

## Observed behavior in the book's installed FLO 0.3.0

The SPPM renderer reads scalar cycle_time, wait_time, and changeover/setup time
values. Labels say CT, WT, and C/O without identifying the statistic. There are
full, compact, and teaching label-density modes, but no dedicated sample-count
or timing-distribution display. Task notes can carry prose; that is not a
substitute for structured measurement semantics.

## Recommended capability

1. Identify the statistic explicitly. A measured mean must be distinguishable
   from a planned duration, estimate, single observation, or median.
2. Support sample count and provenance: dataset/reference, observation window,
   work unit, aggregation level, and whether evidence is simulated or observed.
3. Retain a compact default: role, Avg CT/CO, important Avg WT, and n. A shared
   map caption may supply n when all main activities share the same count;
   exceptions such as correction work need their own counts.
4. Offer an optional detail projection with minimum, median, mean, maximum,
   and P90. Preserve units and the percentile method. Sum and mode may be
   stored when meaningful but need not occupy the default diagram.
5. Show branch frequency with its denominator, e.g. 5 of 39 orders. Distinguish
   affected orders from repeated correction occurrences.
6. Preserve unknown/missing measurements separately from a measured zero.

One possible extension, subject to FLO schema and compatibility review:

```yaml
cycle_time:
  value: 30.4
  unit: min
  statistic: mean
  sample_count: 39
  sample_unit: order_activity_occurrence
  evidence_ref: representative-friday-91
  summary:
    minimum: 26.2
    median: 30.3
    maximum: 35.0
```

This shape is illustrative, not a claim that adding YAML keys is already
supported. Review parsing, validation, canonical IR, exports, rendering, and
static analysis together. Existing scalar inputs need an explicit legacy
interpretation rather than being silently relabeled as measured means.

## Guardrails for analysis

- Summing node means estimates an order mean only with compatible cohorts,
  occurrence frequencies, and additive/nonoverlapping activity intervals.
- A correction branch traversed by 5 of 39 orders contributes its average
  duration times 5/39, provided each affected order traverses it once.
- Parallel subloads must not be blindly summed into customer elapsed time.
  Repeated passes and partial observations also need explicit treatment.
- Never sum node medians, minima, maxima, or P90s and label the result as the
  corresponding end-to-end statistic. Compute those from complete order data.
- A shortest/longest graph path using scalar node means is not an empirical
  minimum/maximum lead time. Label modeled path bounds accordingly.
- A footer summing only promoted queues is not a complete customer lead time.
  Omitted minor waits must either remain in the calculation or cause a clear
  incomplete-estimate label. Do not count a promoted queue twice.
- Rates require matching cohorts and denominators. A mean of daily rates is
  not generally the pooled order-level rate.
- WIP needs an averaging window and boundary. A closing snapshot cannot stand
  in for average WIP in Little's Law.

## Acceptance examples for the FLO team

- Wash CT displays Avg CT 30.4 min, n=39; a detail view can show its profile.
- A correction path displays 5/39 orders and its separate n=5 timing basis.
- A timing field absent from input displays unknown/omitted, not a measured 0.
- An incomplete map does not claim a full observed lead-time total.
- A branched/parallel model does not report an unqualified sum of node times
  as empirical order lead time or P90.
- Book/print output remains readable without hover, tooltips, or color alone.

## Consumer-side approach pending FLO work

The book can use explicit average/sample-count captions and companion timing
tables now. Keep the current renderer's scalar inputs intact and suppress its
aggregate footer where it would be mistaken for a complete measured total.
No FLO implementation or dependency upgrade is requested by this note.
