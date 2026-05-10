---
id: 6d3f7a91
title: Add publication readability diagnostics and strict mode
headline: Define warnings, fallback behavior, and hard failures for unreadable or over-constrained publication output.
priority: high
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-06T00:00:00+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 048bbcb1
blocks: []
actual_start_date: '2026-05-10T00:00:00+00:00'
actual_end_date: '2026-05-10T00:00:00+00:00'
progress_percentage: 100.0
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-10T00:00:00+00:00'
comments: []
github_issue: null
---

## Add publication readability diagnostics and strict mode

Define a reusable diagnostics policy for publication output so renderers can warn, fall back, or fail when readability limits are exceeded.

## Why

Pagination and hierarchy-aware rendering will need explicit policy for when a requested output mode is merely degraded versus impossible. That behavior should not be improvised independently in each renderer.

## Acceptance Criteria

- The platform distinguishes warning conditions from hard publication failures.
- Non-strict modes can fall back automatically with explicit warnings.
- Strict publication mode fails instead of silently changing the requested output mode.
- Renderer adoption guidance is documented well enough for SPPM to use first.

## Notes

This is shared infrastructure, but it is being prioritized because SPPM publication completeness depends on it.
