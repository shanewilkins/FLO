---
id: 4a7e637c
title: Add trace-to-model alignment
headline: Align observed trace events to modeled nodes and paths.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-3-telemetry-alignment
labels: []
remote_ids: {}
created: '2026-05-05T18:56:59.214184+00:00'
updated: '2026-05-05T19:42:39.504892+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 08be4d4e
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

# Add trace-to-model alignment

Align observed traces to modeled nodes and paths.

## Why

Trace-to-model alignment is the core bridge between declarative process models and observed event data. It is the enabling step for node, path, and rework-rate analytics in v0.3.

## Acceptance Criteria

- Observed traces can be aligned to modeled nodes or paths.
- Alignment behavior is defined clearly enough for users to interpret mismatches.
- Representative tests cover aligned and partially aligned scenarios.

## Notes

Keep the initial alignment logic modest and explain any assumptions about identifiers or activity keys.
