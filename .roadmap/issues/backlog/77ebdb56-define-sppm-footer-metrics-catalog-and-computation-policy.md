---
id: 77ebdb56
title: Define SPPM footer metrics catalog and computation policy
headline: ''
priority: medium
status: todo
archived: false
issue_type: feature
milestone: null
labels: []
remote_ids: {}
created: '2026-05-06T23:20:19.934006+00:00'
updated: '2026-05-06T23:20:19.934010+00:00'
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

Decide which analytics belong in the SPPM footer, how each metric is computed, and where those computations should live.

## Why
The footer band now supports supplied metric rows and notes from metadata or render-time inputs, but the project has not yet chosen a canonical set of metrics or derivation rules. That policy should be decided separately so footer plumbing can ship without locking in premature analytics semantics.

## Acceptance Criteria
- The project has an explicit list of candidate footer metrics and their intended audience.
- Each approved metric has a documented computation or data source.
- The issue identifies whether metrics should be precomputed in model metadata, supplied at render time, or derived inside FLO.
- Follow-up implementation issues are created if new compiler or renderer plumbing is required.

## Notes
This issue is intentionally separate from #653b0e4c, which only adds the optional footer-band seam and rendering support.
