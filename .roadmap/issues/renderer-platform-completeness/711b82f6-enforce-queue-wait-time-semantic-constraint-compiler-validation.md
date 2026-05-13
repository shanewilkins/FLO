---
id: 711b82f6
title: Enforce queue/wait_time semantic constraint in compiler
headline: Add compiler validation rejecting wait_time on task nodes; queues only
priority: high
status: done
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- compiler,validation,semantics,sppm
remote_ids: {}
created: '2026-05-13T14:30:00.000000+00:00'
updated: '2026-05-13T14:45:00.000000+00:00'
assignee: shanewilkins
estimated_hours: 0.5
due_date: null
depends_on:
- 699761c3
blocks:
- 712c94a7
- 713d5f8b
- 714e9c2d
actual_start_date: null
actual_end_date: '2026-05-13T14:45:00.000000+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T14:45:00.000000+00:00'
comments: []
github_issue: null
---

# Enforce queue/wait_time semantic constraint in compiler

After rendering the WT vs CO distinction (699761c3), enforce semantic constraints at compile time to prevent confusion.

## Why

- **Pedagogical integrity**: Students must understand queues as distinct problems requiring distinct solutions
- **Shape-semantics alignment**: Queue triangles represent delays; tasks represent work
- **Data model clarity**: `wait_time` can only exist on queue nodes

## Scope

### Phase 1: Add compiler validation rules
- Reject `wait_time` on task/system_task/subprocess nodes
- Reject `cycle_time`/`crossover_time` on queue nodes
- Clear error messages directing users to restructure

### Phase 2-4: Refactor examples (separate issues)
- sppm_feature_showcase.flo: Extract task wait_times to preceding queue nodes
- bakery_setup_vs_queue.flo: Same restructuring pattern
- Update documentation with "Modeling Queues Properly" guidance

### Phase 5: Add comprehensive test coverage
- Valid queue nodes with wait_time
- Invalid task/system_task/subprocess nodes with wait_time
- Invalid queue nodes with cycle/crossover times
- Edge cases (subprocesses, etc.)

### Phase 6: Integration and commit
- Full test suite validation
- All examples rebuild without errors
- Pre-commit checks pass
- Commit to renderer-platform-completeness milestone

## Acceptance Criteria

✓ Compiler rejects wait_time on non-queue nodes with actionable error message
✓ Compiler rejects cycle/crossover times on queue nodes
✓ 9+ compiler validation tests covering all edge cases
✓ All existing examples validate or are refactored successfully
✓ User_Manual.md explains the constraint and restructuring pattern
✓ No existing valid examples break (or are intentionally updated)

## Notes

- Blocks refactoring work in issues 712c94a7, 713d5f8b, 714e9c2d
- Follow-up to 699761c3 (rendering side is done; now enforce on data model side)
- Breaking change: existing FLO files with wait_time on tasks must be restructured
- But this is pedagogically justified—forces correct process modeling
