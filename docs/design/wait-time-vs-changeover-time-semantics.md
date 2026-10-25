# Wait Time vs Changeover Time Semantics

Status: accepted

Normative timing-placement rules now live in `docs/specs/core_language.md`.

This note explains the rationale behind FLO's waiting and setup-time rules.

## Purpose

FLO distinguishes queue delays from setup/changeover delays because they indicate different operational failure modes and require different interventions.

- Queue delay indicates constrained downstream capacity or poor flow control.
- Changeover delay indicates setup/reconfiguration friction in active work steps.

## Data Structure: Representing Queues Explicitly

Queues are first-class nodes (`kind: queue`) instead of optional annotations on tasks.

Why this structure is intentional:

- Shape enforces semantics: queue triangles model waiting, task rectangles model work.
- Diagnostics stay correct: queue metrics are analyzed separately from setup metrics.
- Pedagogy improves: learners must ask "queue problem or setup problem?" before choosing countermeasures.

Normative rule summary:

- `metadata.wait_time` is canonical on `queue` nodes.
- `metadata.wait_before` preserves worksheet waiting evidence on work nodes.
- Task-level source `wait_time` is a compatibility alias normalized to
  `wait_before` during compilation.
- `metadata.cycle_time`, `metadata.crossover_time` (and aliases
  `transfer_time`/`changeover_time`) belong on work nodes (`task`,
  `system_task`, `subprocess`).

The authoritative rule lives in `docs/specs/core_language.md`.

## Modeling Pattern

Worksheet timing attached to a task:

```yaml
- id: bake
  kind: task
  metadata:
    cycle_time: {value: 25, unit: min}
    wait_before: {value: 120, unit: min, measurement_id: bake_wait}
```

The same evidence may be promoted to a queue for visualization:

```yaml
- id: oven_queue
  kind: queue
  metadata:
    wait_time:
      value: 120
      unit: min
      measurement_refs: [bake_wait]

- id: bake
  kind: task
  metadata:
    cycle_time: {value: 25, unit: min}
    wait_before: {value: 120, unit: min, measurement_id: bake_wait}
    crossover_time: {value: 30, unit: min}
```

Static timing counts the task evidence once and does not add the promoted queue
projection again on a path containing the full replacement evidence.

Measurement identity is an assertion, not merely a suppression switch. Repeated
IDs must describe equivalent normalized durations. A queue's `measurement_refs`
asserts the sum of distinct work waits; contradictory amounts or aggregate
definitions are validation errors. Numeric equivalence uses relative tolerance
`1e-9`, absolute tolerance `0`, preserving measured zero.

Deduplication cannot be decided globally before considering alternative paths.
If a queue-traversing path omits any referenced work wait, analysis warns and
withholds a complete elapsed total for that path instead of silently dropping
the queue or guessing a residual. Authored durations remain visible in diagrams,
separate from counted contributions.

An explicit `wait` hold is also time-bearing: absent `wait_time` makes affected
timing incomplete with a warning, not a model-validation failure. These policies
do not infer parallel synchronization or critical-path elapsed time.

## Lean/Six Sigma Alignment

- Queue reduction: pull systems, kanban, takt leveling, WIP limits.
- Setup reduction: SMED, 5S, standard work, changeover checklists.

Treating both as one metric blurs root cause. FLO keeps them separate by structure so analysis and teaching remain accurate.
