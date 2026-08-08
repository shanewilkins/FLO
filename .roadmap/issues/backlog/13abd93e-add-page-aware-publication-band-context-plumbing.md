---
id: 13abd93e
title: Add page-aware publication band context plumbing
headline: ''
priority: medium
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-06T23:01:52.339073+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
- a3e631a8
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

Add shared plumbing for page-aware header and footer context so renderers can populate document bands from publication-series metadata.

Why

Shared document bands and SPPM-specific footer content are already tracked, but there is no explicit issue for wiring page numbers, series identity, parent/child references, and continuation context through the shared publication plan into those bands. That gap will matter once pagination and child maps arrive.

Acceptance Criteria

- Shared publication-band content can carry page number and series context.
- The plumbing supports parent-map, child-map, and continuation references where useful.
- Renderers can populate shared bands from publication metadata without introducing renderer-specific band contracts.
- Existing single-page output remains stable when page context is absent.
- Documentation clarifies which band content is shared infrastructure versus renderer-specific semantics.
