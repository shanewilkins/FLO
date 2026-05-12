---
id: 6f1ad0c3
title: Add wrapped multi-page showcase with explicit continuation overrides
headline: Add a publication-oriented showcase variant that demonstrates deterministic
  continuation anchors across page/process boundaries.
priority: high
status: todo
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,showcase,continuations
remote_ids: {}
created: '2026-05-12T18:40:00+00:00'
updated: '2026-05-12T18:40:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- a3f99e65
- 9c2e4b7a
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

Add a wrapped showcase path that demonstrates continuation anchors in the context where they are semantically correct: wrapped pagination and follow-on subprocess/process boundaries.

Why

Continuation anchor support is implemented and test-covered in renderer code, but the showcase does not yet present a clean, publication-style example that demonstrates automatic wrap-derived anchors plus explicit metadata overrides.

Scope

- Add or update showcase command/output configuration to use wrapped publication settings (for example auto wrap with target columns and named page format).
- Include at least one explicit metadata override (`continuation_to`/`continuation_from` aliases) on an edge where continuation semantics are valid.
- Ensure resulting DOT/SVG artifacts visibly preserve deterministic continuation tokens.
- Avoid duplicating renderer engine tests already covered under `a3f99e65`; this issue is showcase/reference focused.

Acceptance Criteria

- Wrapped showcase output contains semantically valid continuation anchors that are easy to follow.
- At least one explicit override token appears consistently in DOT and SVG outputs.
- Reference artifacts and integration checks are updated for deterministic regeneration.
- The example avoids awkward single-page continuation usage on ordinary mainline edges.
