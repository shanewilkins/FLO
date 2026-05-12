---
id: 47ad9c62
title: Move subprocess detail-map handling to a shared domain seam
headline: Renderer code currently imports subprocess detail-map reference helpers
  from a compiler-internal mod
priority: high
status: closed
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:34.550974+00:00'
updated: '2026-05-12T12:31:13.992965+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-12T12:24:55.277958+00:00'
actual_end_date: null
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

Renderer code currently imports subprocess detail-map reference helpers from a compiler-internal module.

## Why
The helper itself is useful, but its current location couples render code to compiler internals instead of a stable shared contract.

## Acceptance Criteria
- Subprocess detail-map reference helpers live in a shared, renderer-safe module.
- Render and validation code both depend on that shared seam rather than on compiler internals.
- Behavior for detail-map reference resolution remains unchanged.
- Tests cover the shared contract from at least one non-compiler consumer.
