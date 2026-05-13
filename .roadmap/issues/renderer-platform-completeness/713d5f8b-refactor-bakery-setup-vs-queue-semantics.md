---
id: 713d5f8b
title: Refactor bakery_setup_vs_queue to enforce queue semantics
headline: Restructure bakery example to use queue nodes for wait times
priority: high
status: done
archived: false
issue_type: task
milestone: renderer-platform-completeness
labels:
- examples,semantics,sppm,pedagogy
remote_ids: {}
created: '2026-05-13T14:30:00.000000+00:00'
updated: '2026-05-13T15:18:00.000000+00:00'
assignee: shanewilkins
estimated_hours: 0.5
due_date: null
depends_on:
- 711b82f6
blocks:
- 715f2c8a
actual_start_date: '2026-05-13T15:06:00.000000+00:00'
actual_end_date: '2026-05-13T15:18:00.000000+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T15:18:00.000000+00:00'
comments: []
github_issue: null
---

# Refactor bakery_setup_vs_queue to enforce queue semantics

Update the pedagogical bakery example (teaches WT vs CO distinction) to match queue/wait_time constraint.

## Why

The bakery_setup_vs_queue.flo is the key pedagogical example showing the distinction between queue delays and setup time. It currently violates the constraint by having wait_time on task nodes. Fixing it demonstrates the correct semantic structure.

## Current Structure (Problematic)

```
prepare_dough (CT: 5, WT: 5)
  ↓
laminate_queue (WT: 45)
  ↓
laminate (CT: 10, WT: ? )  ← wait_time on task (WRONG)
```

## New Structure (Correct)

```
prepare_dough (CT: 5)
  ↓
prep_queue (WT: 5)  ← NEW queue node
  ↓
laminate_queue (WT: 45)
  ↓
laminate (CT: 10)  ← wait_time removed
  ↓
<other steps following same pattern>
```

## Changes

1. Extract all task-node `wait_time` values into preceding queue nodes
2. Apply pattern consistently across all 11 steps
3. Keep changeover_time (oven_setup) on task nodes as-is
4. Rebuild renders/reference/bakery_setup_vs_queue.{dot,svg}
5. Update footer caption to clarify: queue triangles = delays, task rectangles = work + setup
6. Ensure integration tests (test_sppm_wt_vs_co_acceptance.py) still pass

## Acceptance Criteria

✓ bakery_setup_vs_queue.flo validates without compiler errors
✓ All wait_times extracted to queue nodes
✓ All changeover_times remain on task nodes (oven_setup)
✓ Renders correctly with queue triangles and task boxes properly separated
✓ Integration test_sppm_wt_vs_co_acceptance tests still pass
✓ Footer caption reflects correct semantics
✓ Artifact files rebuilt successfully
✓ Example demonstrates pedagogically that WT and CO are distinct problems
