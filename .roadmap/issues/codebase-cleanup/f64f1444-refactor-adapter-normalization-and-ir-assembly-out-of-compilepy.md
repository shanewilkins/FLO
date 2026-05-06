---
id: f64f1444
title: Refactor adapter normalization and IR assembly out of compile.py
headline: ''
priority: medium
status: todo
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:38.647507+00:00'
updated: '2026-05-06T23:35:38.647519+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: null
actual_end_date: null
progress_percentage: null
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

`compile.py` now carries source-node flattening, attribute normalization, subprocess nesting behavior, and edge synthesis in one file despite being framed as a thin compiler boundary.

## Why
That file has outgrown its conceptual role, which makes the adapter/compiler boundary harder to reason about and raises the cost of future compiler work.

## Acceptance Criteria
- Adapter normalization, source flattening, and IR assembly responsibilities are more cleanly separated.
- `compile.py` becomes a thinner orchestration layer or is reorganized around clearer submodules.
- Existing compile behavior remains fully covered by tests.
- The resulting boundary between adapter concerns and compiler concerns is clearer in code structure.
