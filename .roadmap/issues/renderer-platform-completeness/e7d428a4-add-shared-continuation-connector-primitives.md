---
id: e7d428a4
title: Add shared continuation connector primitives
headline: Build reusable continuation primitives that any renderer can adopt when
  flow resumes elsewhere.
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:37.385797+00:00'
updated: '2026-05-05T19:42:35.773569+00:00'
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

# Add shared continuation connector primitives

Provide reusable continuation connector mechanics that can be applied consistently across SPPM and future renderers.

## Why

SPPM needs continuation markers first, but the underlying mechanics are broader. Shared continuation primitives prevent each renderer from inventing incompatible ways to show that a flow resumes elsewhere.

## Acceptance Criteria

- A renderer-independent continuation primitive is defined.
- SPPM can adopt that primitive without losing notation clarity.
- The primitive is compatible with page and overflow behavior.
- Future renderers can reuse the mechanism without inheriting SPPM-specific visual rules.

## Notes

Keep semantic notation and generic continuation mechanics separate so the platform remains reusable.
