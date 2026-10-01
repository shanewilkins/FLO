---
id: 08be4d4e
title: Define minimal telemetry event schema
headline: Define the smallest useful event schema needed to align traces with modeled flows.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-3-telemetry-alignment
labels: []
remote_ids: {}
created: '2026-05-05T18:56:58.694721+00:00'
updated: '2026-05-05T18:56:58.694724+00:00'
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

# Define minimal telemetry event schema

Define the minimal event schema needed to align traces with declarative models.

## Why

The v0.3 telemetry plan starts with a minimal event schema. Without that contract, alignment and downstream trace analytics remain underspecified.

## Acceptance Criteria

- A minimal event schema is defined for trace alignment use cases.
- Required and optional fields are documented clearly.
- The schema is narrow enough to be practical while supporting later analysis.

## Notes

Keep the schema aligned with observational trace use cases, not full process-mining scope.
