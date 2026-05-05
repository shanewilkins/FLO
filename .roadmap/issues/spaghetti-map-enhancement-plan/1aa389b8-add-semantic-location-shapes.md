---
id: 1aa389b8
title: Add semantic location shapes
headline: Use distinct visual shapes for different location kinds in spaghetti maps.
priority: medium
status: blocked
archived: false
issue_type: feature
milestone: spaghetti-map-enhancement-plan
labels: []
remote_ids: {}
created: '2026-05-05T18:57:02.274074+00:00'
updated: '2026-05-05T22:55:36.287809+00:00'
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

# Add semantic location shapes

Use distinct location shapes for different location kinds in spaghetti maps.

## Why

Semantic location shapes help readers distinguish storage, prep, transit, and other area types at a glance. This makes the spatial model more expressive without changing route inference.

## Acceptance Criteria

- Location metadata can express location kind.
- Spaghetti output maps location kinds to distinct shapes or styles.
- Unknown or unspecified kinds fall back to a default rendering.

## Notes

Keep the kind-to-style mapping configurable enough for later refinement.
