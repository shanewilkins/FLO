---
id: 1a782931
title: Add dual movement channels
headline: Support separate people and material movement channels in spaghetti maps.
priority: high
status: blocked
archived: false
issue_type: feature
milestone: spaghetti-map-enhancement-plan
labels: []
remote_ids: {}
created: '2026-05-05T18:57:00.765589+00:00'
updated: '2026-05-05T22:54:13.177543+00:00'
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

# Add dual movement channels

Support separate material and people movement channels in spaghetti maps.

## Why

The spaghetti enhancement plan starts by separating material movement from people movement. Without that split, the diagram cannot distinguish two fundamentally different movement behaviors.

## Acceptance Criteria

- Spaghetti analysis can represent material and people movement as separate channels.
- Users can render one channel or both without conflating them.
- Tests cover examples with worker assignments and location changes.

## Notes

Keep typed movement records separate even when routes overlap visually.
