---
id: 7b6badf5
title: Add analysis-oriented diagnostics and reports
headline: Expose static analysis results through diagnostics and report-friendly outputs.
priority: medium
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:58.199667+00:00'
updated: '2026-05-05T20:15:49.696498+00:00'
assignee: shanewilkins
estimated_hours: null
due_date: null
depends_on:
- 4dc01dd3
- ffebc1cc
- f00d777a
- 6a61c515
- d3baa2d2
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

# Add analysis-oriented diagnostics and reports

Produce user-facing diagnostics and report surfaces for static Lean analysis.

## Why

Metrics alone are not enough; users need analysis results exposed in a readable form. This closes the gap between internal analysis computation and practical Lean-oriented output.

## Acceptance Criteria

- Static analysis results are surfaced in a user-facing diagnostic or report format.
- Outputs are understandable without reading internal IR structures directly.
- Coverage exists for representative reporting scenarios.

## Notes

Keep report formatting decoupled from any one diagram renderer.
