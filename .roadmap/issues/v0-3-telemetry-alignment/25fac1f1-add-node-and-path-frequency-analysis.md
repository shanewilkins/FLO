---
id: 25fac1f1
title: Add node and path frequency analysis
headline: Compute node visit and path frequency metrics from aligned traces.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-3-telemetry-alignment
labels: []
remote_ids: {}
created: '2026-05-05T18:56:59.752912+00:00'
updated: '2026-05-05T19:42:40.124245+00:00'
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

# Add node and path frequency analysis

Compute node visit and path frequency metrics from aligned trace data.

## Why

Once traces can be aligned to the model, node and path frequency become natural first-order analytics. They are explicitly part of the telemetry-alignment roadmap and provide the clearest early value from aligned trace data.

## Acceptance Criteria

- Node visit frequency can be computed from aligned traces.
- Path frequency can be computed or summarized from aligned traces.
- Tests cover representative aligned-trace scenarios.

## Notes

Keep the frequency outputs reusable for later reporting or visualization layers.
