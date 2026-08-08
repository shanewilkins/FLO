---
id: 63da7b5d
title: Consolidate render option schema and CLI plumbing
headline: Render option definitions, CLI option construction, and option/output compatibility
  checks are curre
priority: high
status: closed
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:35.367007+00:00'
updated: '2026-05-12T12:20:10.123715+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-11T19:04:45.065839+00:00'
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

Render option definitions, CLI option construction, and option/output compatibility checks are currently maintained in parallel paths.

## Why
That duplication will drift as the renderer surface grows and makes every new option more expensive to add safely.

## Acceptance Criteria
- Render option definitions have a single authoritative schema or registry.
- CLI wiring and compatibility validation derive from that shared source instead of hardcoded duplicated lists.
- Adding a new render option requires touching fewer places than today.
- Existing CLI and render-option tests continue to pass.
