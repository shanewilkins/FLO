---
id: 5fbc5f50
title: Reduce dict marshalling between canonical IR and SPPM rendering
headline: The SPPM renderer currently re-shapes typed IR objects into ad hoc dictionaries
  before doing most of
priority: medium
status: closed
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:36.196857+00:00'
updated: '2026-05-12T12:48:47.083386+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-12T12:40:25.381823+00:00'
actual_end_date: null
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: null
comments: []
github_issue: null
---

The SPPM renderer currently re-shapes typed IR objects into ad hoc dictionaries before doing most of its work.

## Why
That transformation duplicates schema knowledge, increases defensive typing code, and creates drift risk between canonical IR and render-time data shapes.

## Acceptance Criteria
- The SPPM renderer consumes a more stable typed or explicitly normalized intermediate shape.
- Canonical IR fields are not redundantly re-described across multiple renderer helpers.
- The remaining normalization seam is narrow and well-tested.
- Existing SPPM behavior remains unchanged.
