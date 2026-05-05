---
id: ffebc1cc
title: Add rework-loop detection analysis
headline: Detect and summarize rework loops as part of the static analytics layer.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:56.215463+00:00'
updated: '2026-05-05T18:56:56.215465+00:00'
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

# Add rework-loop detection analysis

Detect and summarize rework loops from canonical IR structures.

## Why

Rework-loop detection is explicitly part of the v0.2 analytics outline and is central to identifying waste-heavy paths in a modeled process.

## Acceptance Criteria

- Analysis can detect rework loops from canonical IR topology.
- Output distinguishes rework from ordinary cyclic structure where the model provides that information.
- Results are covered by tests using representative looping examples.

## Notes

This issue is about analysis and reporting, not about SPPM rework rendering.
