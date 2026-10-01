---
id: 22341a80
title: Add facility boundary and area context
headline: Provide a boundary or area backdrop so spaghetti routes have spatial context.
priority: medium
status: blocked
archived: false
issue_type: feature
milestone: spaghetti-map-enhancement-plan
labels: []
remote_ids: {}
created: '2026-05-05T18:57:01.768342+00:00'
updated: '2026-05-05T22:55:06.936673+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
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

# Add facility boundary and area context

Render facility boundaries or area context as a background layer in spaghetti maps.

## Why

Spaghetti routes are more interpretable when readers can see the overall facility or area shape. This adds context without changing the core movement semantics.

## Acceptance Criteria

- Spaghetti maps can render a facility boundary or area context layer when metadata is present.
- Omission of boundary metadata preserves existing behavior.
- The boundary layer remains visually non-intrusive.

## Notes

Start with simple boundary forms before considering more complex polygon support.
