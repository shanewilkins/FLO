---
id: 699761c3
title: Differentiate crossover time from waiting time in SPPM
headline: Add explicit distinction between crossover/transfer time and waiting time
  in SPPM semantics and rend
priority: medium
status: done
archived: false
issue_type: feature
milestone: renderer-platform-completeness
labels:
- sppm,metrics,semantics
remote_ids: {}
created: '2026-05-11T17:22:38.096691+00:00'
updated: '2026-05-13T15:42:00+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 77ebdb56
blocks: []
actual_start_date: '2026-05-12T22:00:00+00:00'
actual_end_date: '2026-05-13T15:42:00+00:00'
progress_percentage: 100
handoff_notes: null
previous_assignee: null
handoff_date: null
git_branches: []
git_commits: []
completed_date: '2026-05-13T15:42:00+00:00'
comments: []
github_issue: null
---

Add explicit distinction between crossover/transfer time and waiting time in SPPM semantics and rendering.\n\nScope\n- Define canonical fields/labels for crossover time vs waiting time.\n- Render both clearly in node/edge callouts and footer metrics when present.\n- Ensure computations/data-source expectations are documented.\n\nAcceptance Criteria\n- Waiting and crossover times can coexist without ambiguity.\n- Footer metrics policy references both measures where appropriate.\n- Tests verify formatting and precedence rules.\n- Documentation includes examples showing the distinction.

Progress Update (2026-05-12)
- Added canonical crossover extraction precedence in render metadata helpers:
  - `crossover_time` > `transfer_time` > `changeover_time` (legacy alias).
- Updated SPPM node metric rendering to use `CO: ... crossover` semantics while preserving `WT: ... wait` for waiting time.
- Added tests for canonical precedence and transfer-time alias handling in SPPM node rendering.
- Added publication/footer metric test coverage showing explicit waiting vs crossover distinction.
- Documented the waiting vs crossover policy and examples in the user manual.
