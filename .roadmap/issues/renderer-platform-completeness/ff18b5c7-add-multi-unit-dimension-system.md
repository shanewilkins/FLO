---
id: ff18b5c7
title: Add multi-unit dimension system
headline: Support dimension inputs in multiple units instead of forcing pixel-only layout constraints.
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-05T17:17:35.081820+00:00'
updated: '2026-05-05T17:17:35.081822+00:00'
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

# Add multi-unit dimension system

Support render and layout dimensions in px, in, and cm so future document-grade outputs are not bound to pixel-only configuration.

## Why

The current layout constraints are pixel-only, but document-grade rendering needs user-facing dimensions that map to real page and print sizes. This is a foundational platform task for reusable rendering controls.

## Acceptance Criteria

- Dimension inputs accept at least `px`, `in`, and `cm`.
- Internal layout logic normalizes those units consistently.
- CLI and render options validate malformed or unsupported dimension strings.
- Tests cover parsing, conversion, and boundary conditions.

## Notes

This issue should produce a reusable dimension type rather than scattering ad hoc conversions across renderers.
