---
id: 114c6965
title: Generalize annotation and callout layout
headline: Extract shared placement rules for annotations, callouts, and nearby explanatory boxes.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:37.925760+00:00'
updated: '2026-05-05T17:17:37.925762+00:00'
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

# Generalize annotation and callout layout

Extract shared annotation and callout placement logic from renderer-specific implementations so labels and data boxes can be managed consistently.

## Why

Annotation and callout placement is already showing up in renderer-specific postprocessing. Pulling out the reusable placement logic now reduces duplication and avoids baking SPPM quirks into the general rendering stack.

## Acceptance Criteria

- Shared placement rules exist for nearby annotation or callout elements.
- SPPM-specific postprocessing can adopt the shared logic incrementally.
- The shared logic avoids obvious overlaps with primary flow geometry where feasible.
- Renderers that do not use callouts remain unaffected.

## Notes

This issue is about placement mechanics, not about standardizing every annotation visual style across renderers.
