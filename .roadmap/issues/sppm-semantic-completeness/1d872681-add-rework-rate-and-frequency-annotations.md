---
id: 1d872681
title: Add rework rate and frequency annotations
headline: Render explicit rates or frequencies on rework edges in SPPM output.
priority: high
status: todo
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T18:57:03.273199+00:00'
updated: '2026-05-06T17:05:37.545362+00:00'
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

# Add rework rate and frequency annotations

Render rate and frequency labels on rework edges in SPPM outputs.

## Why

Rework loops are more useful when they quantify how often they occur. Rate and frequency annotations turn rework from a structural marker into a prioritization aid.

## Acceptance Criteria

- Rework edge metadata can carry rate or frequency information.
- SPPM output renders that information clearly on rework edges.
- Validation handles invalid or ambiguous rate values reasonably.
- Tests cover representative rework examples.

## Notes

Keep rate semantics separate from telemetry-derived calculations, which belong under telemetry alignment.
