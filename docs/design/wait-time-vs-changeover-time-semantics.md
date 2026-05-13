# Wait Time vs Changeover Time Semantics

This note defines the modeling semantics FLO enforces for waiting and setup time.

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

Compiler-enforced constraints:

- `metadata.wait_time` is valid only on `queue` nodes.
- `metadata.cycle_time`, `metadata.crossover_time` (and aliases `transfer_time`/`changeover_time`) belong on work nodes (`task`, `system_task`, `subprocess`).

## Modeling Pattern

Invalid pattern:

```yaml
- id: bake
  kind: task
  metadata:
    cycle_time: {value: 25, unit: min}
    wait_time: {value: 120, unit: min}
```

Valid pattern:

```yaml
- id: oven_queue
  kind: queue
  metadata:
    wait_time: {value: 120, unit: min}

- id: bake
  kind: task
  metadata:
    cycle_time: {value: 25, unit: min}
    crossover_time: {value: 30, unit: min}
```

## Lean/Six Sigma Alignment

- Queue reduction: pull systems, kanban, takt leveling, WIP limits.
- Setup reduction: SMED, 5S, standard work, changeover checklists.

Treating both as one metric blurs root cause. FLO keeps them separate by structure so analysis and teaching remain accurate.
