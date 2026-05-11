---
id: d4183d06
title: 'Renderer architecture boundary: shared core vs SPPM-specific vs swimlane-specific'
headline: Define and implement architecture boundaries now that SPPM is maturing,
  to maximize reuse in swimlan
priority: high
status: todo
archived: false
issue_type: other
milestone: renderer-platform-completeness
labels:
- architecture,renderer,swimlane,sppm
remote_ids: {}
created: '2026-05-11T17:23:14.555793+00:00'
updated: '2026-05-11T17:27:11.009581+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 114c6965
- 63da7b5d
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

Define and implement architecture boundaries now that SPPM is maturing, to maximize reuse in swimlane and future renderers.\n\nScope\n- Identify shared renderer primitives (label policy, callout placement, publication bands, option plumbing).\n- Explicitly mark SPPM-only logic (queue triangles, rework semantics, SPPM publication conventions).\n- Define swimlane-specific responsibilities and migration plan for shared pieces.\n\nAcceptance Criteria\n- Written boundary map/ADR exists and is referenced by implementation issues.\n- At least one shared component is consumed by both SPPM and another renderer path.\n- New renderer work does not reintroduce SPPM coupling into shared modules.\n- Team can explain where a new rendering feature should live without ambiguity.
