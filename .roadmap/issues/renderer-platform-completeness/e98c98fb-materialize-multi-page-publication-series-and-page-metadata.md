---
id: e98c98fb
title: Materialize multi-page publication series and page metadata
headline: ''
priority: high
status: closed
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels: []
remote_ids: {}
created: '2026-05-06T23:01:40.232753+00:00'
updated: '2026-05-10T00:00:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 07cb2436
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

Implement explicit multi-page publication-series realization from the shared publication plan, including stable page identifiers and sequence metadata.

Why

The publication model now exists in memory, but the roadmap does not yet track the step where one logical publication becomes one or more concrete pages with stable page ids, page numbers, and series metadata. That implementation is distinct from defining pagination policy.

Acceptance Criteria

- Publication planning can materialize one or more pages for a series instead of assuming a single page.
- Each page carries stable page identifiers and sequence metadata.
- Page metadata is available to renderers without re-deriving semantics from raw IR.
- The implementation stays renderer-agnostic even if SPPM is the first adopter.
- Tests cover deterministic page identity and ordering for the same input and options.
