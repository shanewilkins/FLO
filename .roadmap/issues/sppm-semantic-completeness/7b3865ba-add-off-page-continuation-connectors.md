---
id: 7b3865ba
title: Add off-page continuation connectors
headline: Represent flow continuation cleanly when an SPPM map resumes elsewhere.
priority: high
status: todo
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:33.329455+00:00'
updated: '2026-05-05T19:42:38.890237+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- e7d428a4
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

# Add off-page continuation connectors

Introduce continuation symbols for flows that resume elsewhere or on another page while preserving clear SPPM semantics.

## Why

Continuation markers are necessary once maps exceed a single self-contained canvas or need to reference detail maps. Without them, splitting or continuing a flow breaks the semantics of the rendered process.

## Acceptance Criteria

- SPPM output can render explicit continuation markers for flows that resume elsewhere.
- Continuation labels or references are stable and understandable to readers.
- Existing edge routing and annotations continue to render correctly around continuation markers.
- The notation can be reused later by shared renderer-platform primitives where appropriate.

## Notes

This is the SPPM-facing semantic issue; generalized continuation mechanics belong under renderer platform completeness.
