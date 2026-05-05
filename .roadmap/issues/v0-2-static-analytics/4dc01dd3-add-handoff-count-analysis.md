---
id: 4dc01dd3
title: Add handoff count analysis
headline: Compute handoff counts from canonical IR to support static Lean analysis.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:55.706092+00:00'
updated: '2026-05-05T18:56:55.706094+00:00'
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

# Add handoff count analysis

Compute handoff counts from canonical IR to support static Lean analysis.

## Why

Handoff count is one of the core static measures called out in the legacy v0.2 analytics plan. It is a foundational metric for waste analysis and should exist as a first-class analysis output.

## Acceptance Criteria

- Analysis can compute handoff counts from canonical IR.
- The metric is documented clearly enough for users to interpret it.
- Tests cover representative flows with varying handoff structures.

## Notes

Keep the computation on canonical IR rather than render-specific artifacts.
