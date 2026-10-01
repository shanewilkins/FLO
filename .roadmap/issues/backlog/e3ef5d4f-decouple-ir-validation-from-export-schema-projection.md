---
id: e3ef5d4f
title: Decouple IR validation from export schema projection
headline: Validation currently depends on export-layer schema projection helpers,
  which inverts the intended l
priority: high
status: closed
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:32.896298+00:00'
updated: '2026-05-06T23:53:54.172258+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-06T23:50:52.798422+00:00'
actual_end_date: '2026-05-06T23:53:54.059802+00:00'
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

Validation currently depends on export-layer schema projection helpers, which inverts the intended layering between compiler/validation and export.

## Why
Validation should be able to assert structural and semantic correctness without importing the export package. Keeping that dependency backwards makes validation fragile to export refactors and weakens architectural boundaries.

## Acceptance Criteria
- `flo.compiler.ir.validate` no longer imports from `flo.export`.
- Any schema-shaping helper used by validation lives in a neutral or validation-owned layer.
- Existing validation behavior remains covered by tests.
- Import boundaries stay consistent with repository policy checks.
