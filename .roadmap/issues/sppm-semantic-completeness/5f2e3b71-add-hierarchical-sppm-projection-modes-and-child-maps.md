---
id: 5f2e3b71
title: Add hierarchical SPPM projection modes and child maps
headline: Support collapsed parent maps, subprocess child maps, and bounded inline
  expansion from the same FLO source.
priority: critical
status: todo
archived: false
issue_type: feature
milestone: sppm-semantic-completeness
labels: []
remote_ids: {}
created: '2026-05-06T00:00:00+00:00'
updated: '2026-05-06T17:05:35.113407+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- ce07a4e0
- 07cb2436
- 048bbcb1
blocks:
- 47c38a4e
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

## Add hierarchical SPPM projection modes and child maps

Implement hierarchy-aware SPPM publication modes so the same FLO source can render a collapsed top-level map, subprocess-focused child maps, and bounded inline expansion when readability allows.

## Why

Subprocess notation alone is not enough to make long processes publishable. SPPM needs a coherent hierarchy model so subprocesses become drill-down boundaries rather than ordinary task boxes with ambiguous semantics.

## Acceptance Criteria

- Default top-level SPPM output collapses subprocesses.
- FLO can emit subprocess-focused child SPPM maps from the same authored model.
- Child maps include parent, entry, and exit context.
- Inline subprocess expansion is optional, static, and bounded by readability policy.
- Expansion falls back predictably when publication constraints would be violated.

## Notes

Keep this issue focused on SPPM projection semantics. Shared page, series, and overflow infrastructure belongs under renderer-platform completeness.
