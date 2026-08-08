---
id: 500b4414
title: Split the SPPM DOT renderer into focused modules
headline: 'The SPPM DOT renderer has accumulated graph assembly, input normalization,
  label construction, band '
priority: high
status: closed
archived: false
issue_type: other
milestone: codebase-cleanup
labels: []
remote_ids: {}
created: '2026-05-06T23:35:33.741874+00:00'
updated: '2026-05-06T23:48:57.988039+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on: []
blocks: []
actual_start_date: '2026-05-06T23:39:35.900668+00:00'
actual_end_date: '2026-05-06T23:48:57.872717+00:00'
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

The SPPM DOT renderer has accumulated graph assembly, input normalization, label construction, band rendering, and footer/header concerns in one hotspot file.

## Why
That concentration makes the renderer the highest-risk maintenance surface in the repo and raises the cost of every new SPPM feature.

## Acceptance Criteria
- The current SPPM renderer is broken into smaller modules with clear responsibilities.
- Graph assembly, data extraction, and band/label rendering are no longer co-located in one god module.
- Public behavior remains unchanged and existing SPPM tests still pass.
- The resulting module boundaries are documented in code comments or a design note where needed.
