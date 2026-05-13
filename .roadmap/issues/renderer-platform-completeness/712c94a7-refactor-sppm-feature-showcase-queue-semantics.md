---
id: 712c94a7
title: Refactor sppm_feature_showcase to enforce queue semantics
headline: Restructure showcase example to use queue nodes for wait times
priority: high
status: done
archived: false
issue_type: task
milestone: renderer-platform-completeness
labels:
- examples,semantics,sppm
remote_ids: {}
created: '2026-05-13T14:30:00.000000+00:00'
updated: '2026-05-13T15:05:00.000000+00:00'
assignee: shanewilkins
estimated_hours: 0.5
due_date: null
depends_on:
- 711b82f6
blocks:
- 715f2c8a
actual_start_date: '2026-05-13T14:45:00.000000+00:00'
actual_end_date: '2026-05-13T15:05:00.000000+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T15:05:00.000000+00:00'
comments: []
github_issue: null
---

# Refactor sppm_feature_showcase to enforce queue semantics

Update the showcase example to match the queue/wait_time constraint.

## Why

The sppm_feature_showcase.flo currently has wait_time on task nodes (intake, assess_scope, execute_service, etc.), which violates the semantic constraint being enforced in 711b82f6.

## Current Structure (Problematic)

```
intake (CT: 4, WT: 2)  ← wait_time on task (WRONG)
  ↓
triage
  ↓
assess_scope (CT: 5, WT: 1, CO: 3)  ← wait_time on task (WRONG)
```

## New Structure (Correct)

```
intake (CT: 4)
  ↓
intake_queue (WT: 2)  ← NEW queue node
  ↓
triage
  ↓
process_queue (WT: 7)  ← Already exists
  ↓
assess_scope (CT: 5, CO: 3)  ← wait_time removed
  ↓
scope_queue (WT: 1)  ← NEW queue node
  ↓
execute_service (CT: 13)  ← wait_time removed
  ↓
execute_queue (WT: 6)  ← NEW queue node
```

## Changes

1. Remove `wait_time` from: intake, assess_scope, execute_service, complete, dispatch_queue
2. Add new queue nodes: intake_queue, scope_queue, execute_queue, complete_queue, dispatch_delay
3. Update transitions to route through new queues
4. Rebuild renders/reference/sppm_feature_showcase.{dot,svg}
5. Update footer caption to explain queue-node structure

## Acceptance Criteria

✓ sppm_feature_showcase.flo validates without compiler errors
✓ File renders without warnings
✓ All new queue nodes appear in DOT output with WT labels
✓ Task nodes show only CT and CO (no WT)
✓ Artifact files rebuilt successfully
✓ Changes demonstrate the constraint visually
