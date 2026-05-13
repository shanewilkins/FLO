---
id: 715a1d9c
title: Add compiler validation tests for queue/task semantics
headline: Test coverage for wait_time constraint enforcement
priority: high
status: done
archived: false
issue_type: testing
milestone: renderer-platform-completeness
labels:
- testing,compiler,validation,semantics
remote_ids: {}
created: '2026-05-13T14:30:00.000000+00:00'
updated: '2026-05-13T15:42:00.000000+00:00'
assignee: shanewilkins
estimated_hours: 0.5
due_date: null
depends_on:
- 711b82f6
blocks:
- 715f2c8a
actual_start_date: '2026-05-13T14:35:00.000000+00:00'
actual_end_date: '2026-05-13T15:42:00.000000+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T15:42:00.000000+00:00'
comments: []
github_issue: null
---

# Add compiler validation tests for queue/task semantics

Comprehensive test coverage for the queue/wait_time semantic constraint validation.

## Test File

Create `tests/compiler/test_queue_wait_time_validation.py` with 9+ test cases:

### Valid Scenarios

1. `test_queue_node_with_wait_time_is_valid()`
   - Queue node with wait_time should pass validation

2. `test_task_node_with_cycle_time_is_valid()`
   - Task node with only cycle_time should pass

3. `test_task_node_with_crossover_time_is_valid()`
   - Task node with only crossover_time should pass

4. `test_task_node_with_cycle_and_crossover_is_valid()`
   - Task node with both cycle_time and crossover_time should pass

5. `test_task_node_with_no_timing_metadata_is_valid()`
   - Task node with no timing metadata should pass

### Invalid Scenarios

6. `test_task_node_with_wait_time_raises_error()`
   - Task node with wait_time should fail with clear message

7. `test_system_task_node_with_wait_time_raises_error()`
   - System_task node with wait_time should fail

8. `test_subprocess_node_with_wait_time_raises_error()`
   - Subprocess node with wait_time should fail

9. `test_queue_node_with_cycle_time_raises_error()`
   - Queue node with cycle_time should fail

10. `test_queue_node_with_crossover_time_raises_error()`
    - Queue node with crossover_time should fail

### Error Messages

Verify error messages are actionable:
- Task node error: "wait_time is only valid on queue nodes. Restructure: insert a queue node before this task."
- Queue node error: "Queue nodes represent delays only; use wait_time. Cycle and crossover times belong on task nodes."

## Acceptance Criteria

✓ 9+ test cases covering all combinations
✓ Both valid and invalid scenarios tested
✓ Error messages validated for clarity and actionability
✓ All tests passing
✓ Test file integrated into compiler test suite
✓ Coverage report shows validation logic is exercised
