---
id: be4f77ea
title: Add worker-specific traces and styling
headline: Make people-flow traces distinguishable per worker rather than only in aggregate.
priority: high
status: blocked
archived: false
issue_type: feature
milestone: spaghetti-map-enhancement-plan
labels: []
remote_ids: {}
created: '2026-05-05T18:57:01.264911+00:00'
updated: '2026-05-05T22:54:17.936388+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 1a782931
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

# Add worker-specific traces and styling

Render worker-specific traces with deterministic styling and labels.

## Why

Once people movement exists, the next practical need is to distinguish one worker from another. Aggregate people-flow alone is not sufficient for diagnostic or teaching use.

## Acceptance Criteria

- People traces can be rendered per worker.
- Worker traces use deterministic styling or labeling.
- Dense views can still fall back to an aggregate mode where appropriate.

## Notes

Prefer stable styling rules so repeated renders remain comparable.
