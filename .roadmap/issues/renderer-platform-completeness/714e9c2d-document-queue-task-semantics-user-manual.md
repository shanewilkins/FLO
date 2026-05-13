---
id: 714e9c2d
title: Document queue/task semantic constraint in User Manual
headline: Add guidance on modeling queues and tasks correctly in SPPM
priority: high
status: done
archived: false
issue_type: documentation
milestone: renderer-platform-completeness
labels:
- documentation,semantics,sppm
remote_ids: {}
created: '2026-05-13T14:30:00.000000+00:00'
updated: '2026-05-13T15:35:00.000000+00:00'
assignee: shanewilkins
estimated_hours: 0.5
due_date: null
depends_on:
- 711b82f6
blocks:
- 715f2c8a
actual_start_date: '2026-05-13T15:20:00.000000+00:00'
actual_end_date: '2026-05-13T15:35:00.000000+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T15:35:00.000000+00:00'
comments: []
github_issue: null
---

# Document queue/task semantic constraint in User Manual

Update FLO documentation to explain and justify the queue/task semantic constraint.

## Why

When the compiler starts enforcing the constraint in 711b82f6, users need clear documentation explaining:
- What the constraint is
- Why it exists (pedagogical + semantic clarity)
- How to restructure existing FLO files
- Examples of correct vs incorrect patterns

## Changes

### User_Manual.md

Add new section "Modeling Queues and Process Steps" with:

1. **Core Constraint**
   - Queue nodes (kind: queue) use `wait_time` metadata
   - Task nodes (kind: task/system_task/subprocess) use `cycle_time` and `crossover_time`
   - Why: Queues are delays; tasks are work. Different shapes, different semantics.

2. **Lean Alignment**
   - Reference Shingo's distinction: waiting (queue) vs setup (changeover)
   - Queue reduction: pull systems, kanban, takt leveling
   - Setup reduction: 5S, SMED, standardization
   - These require different analyses; the constraint enforces diagnostic clarity

3. **Pattern: "Task with queue delay"**
   ```
   BAD: task_node (CT: 10, WT: 5)
   GOOD:
     - queue_node (WT: 5)
     - task_node (CT: 10)
   ```

4. **Restructuring Guide**
   - Step 1: Identify task nodes with wait_time
   - Step 2: Create preceding queue nodes
   - Step 3: Move wait_time metadata from task to queue
   - Step 4: Re-validate with compiler

5. **Real-world Example**
   - Show before/after for sppm_feature_showcase or bakery example

### docs/design/wait-time-vs-changeover-time-semantics.md

Add subsection "Data Structure: Representing Queues Explicitly":
- Explain why queue nodes are first-class shapes
- Show how structure enforces semantics
- Connect to pedagogical goal: students learn to identify and separate queue delays from setup delays

## Acceptance Criteria

✓ New section "Modeling Queues and Process Steps" added to User_Manual.md
✓ Constraint clearly documented with justification
✓ Bad/good pattern examples shown
✓ Restructuring guide provided for users
✓ Real-world example demonstrates correct pattern
✓ Lean framework connection explained
✓ docs/design file updated with data structure rationale
✓ All cross-references correct
