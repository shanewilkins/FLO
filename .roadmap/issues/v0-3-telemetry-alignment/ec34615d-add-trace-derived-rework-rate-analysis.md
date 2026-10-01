---
id: ec34615d
title: Add trace-derived rework-rate analysis
headline: Derive rework-rate style metrics from aligned telemetry traces.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-3-telemetry-alignment
labels: []
remote_ids: {}
created: '2026-05-05T18:57:00.269032+00:00'
updated: '2026-05-05T19:42:40.745867+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 4a7e637c
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

# Add trace-derived rework-rate analysis

Compute rework-rate style metrics from aligned telemetry traces.

## Why

Rework-rate computation is one of the most directly useful telemetry-derived metrics for process improvement. It extends static structural analysis with evidence from observed traces.

## Acceptance Criteria

- Rework-rate style metrics can be computed from aligned trace data.
- The method and assumptions are documented clearly enough for interpretation.
- Tests cover representative trace patterns with rework behavior.

## Notes

This should build on alignment outputs rather than reimplementing alignment logic.
