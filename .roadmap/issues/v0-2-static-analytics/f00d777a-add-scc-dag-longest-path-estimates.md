---
id: f00d777a
title: Add SCC-DAG longest-path estimates
headline: Estimate longest-path style metrics on condensed SCC-DAG representations.
priority: high
status: todo
archived: false
issue_type: feature
milestone: v0-2-static-analytics
labels: []
remote_ids: {}
created: '2026-05-05T18:56:56.715185+00:00'
updated: '2026-05-05T18:56:56.715187+00:00'
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

# Add SCC-DAG longest-path estimates

Estimate longest-path and lead-time style metrics on condensed SCC-DAGs.

## Why

The v0.2 outline explicitly calls out longest-path estimates on the SCC-DAG. That analysis is a natural bridge between structural modeling and Lean-oriented timing heuristics.

## Acceptance Criteria

- The analysis layer can compute longest-path style estimates on condensed SCC-DAGs.
- Cyclic structure is handled through condensation rather than naive path expansion.
- Tests cover both acyclic and cyclic examples.

## Notes

Keep these estimates clearly labeled as static heuristics, not runtime simulation.
